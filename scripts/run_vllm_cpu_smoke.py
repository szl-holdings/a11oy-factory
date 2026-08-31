#!/usr/bin/env python3
"""Execute a pinned vLLM CPU inference and emit a scoped runtime proof."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _base_version(value: str) -> str:
    return value.split("+", 1)[0]


def _model_license(info: Any) -> str | None:
    card_data = getattr(info, "card_data", None)
    if card_data is None:
        return None
    if isinstance(card_data, dict):
        value = card_data.get("license")
    else:
        value = getattr(card_data, "license", None)
    return str(value) if value else None


def _validate_contract(spec: dict[str, Any], materialization: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema") != "a11oy.factory.runtime-smoke/v1":
        raise RuntimeError("unsupported runtime smoke schema")
    if spec.get("target") != "linux-amd64-cpu":
        raise RuntimeError("this executor only certifies the linux-amd64-cpu smoke target")

    component_id = str(spec.get("runtime_component") or "")
    records = materialization.get("artifacts")
    if materialization.get("ok") is not True or materialization.get("decision") != "ALLOW":
        raise RuntimeError("runtime wheel materialization was not ALLOW")
    if not isinstance(records, list) or len(records) != 1:
        raise RuntimeError("runtime smoke requires exactly one materialized wheel")
    record = records[0]
    if not isinstance(record, dict) or record.get("component") != component_id:
        raise RuntimeError("materialized component does not match runtime contract")
    if record.get("status") not in {"DOWNLOADED_VERIFIED", "REUSED_VERIFIED"}:
        raise RuntimeError("runtime wheel bytes were not verified")
    wheel_path = Path(str(record.get("path") or ""))
    if not wheel_path.is_file():
        raise RuntimeError(f"verified runtime wheel is missing: {wheel_path}")
    wheel_size, wheel_digest = _sha256_file(wheel_path)
    if wheel_size != int(record.get("size", -1)) or wheel_digest != record.get("sha256"):
        raise RuntimeError("runtime wheel changed after materialization")
    return {
        "component": component_id,
        "path": str(wheel_path),
        "size": wheel_size,
        "sha256": wheel_digest,
        "origin_host": record.get("origin_host"),
        "final_host": record.get("final_host"),
        "materialization_receipt_hash": materialization.get("receipt_hash"),
        "lock_digest": materialization.get("lock_digest"),
    }


def execute(spec_path: Path, materialization_path: Path, output_path: Path) -> dict[str, Any]:
    spec = _read_json(spec_path)
    materialization = _read_json(materialization_path)
    wheel = _validate_contract(spec, materialization)

    inference = spec["inference"]
    model_contract = spec["model"]
    model_id = str(model_contract["id"])
    revision = str(model_contract["revision"])
    expected_license = str(model_contract["license"])

    os.environ.setdefault("VLLM_TARGET_DEVICE", "cpu")
    os.environ.setdefault("VLLM_CPU_KVCACHE_SPACE", str(inference["kv_cache_gib"]))
    os.environ.setdefault("VLLM_CPU_OMP_THREADS_BIND", "nobind")
    os.environ.setdefault("OMP_NUM_THREADS", str(inference["omp_threads"]))
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    from huggingface_hub import HfApi, snapshot_download

    hub_started = time.perf_counter()
    info = HfApi().model_info(model_id, revision=revision, files_metadata=True)
    observed_revision = str(getattr(info, "sha", "") or "")
    if observed_revision != revision:
        raise RuntimeError(
            f"model revision mismatch: observed={observed_revision!r} expected={revision!r}"
        )
    observed_license = _model_license(info)
    if (observed_license or "").lower() != expected_license.lower():
        raise RuntimeError(
            f"model license mismatch: observed={observed_license!r} expected={expected_license!r}"
        )

    snapshot_path = Path(
        snapshot_download(
            repo_id=model_id,
            revision=revision,
            allow_patterns=list(model_contract["allow_patterns"]),
        )
    )
    model_file = snapshot_path / "model.safetensors"
    if not model_file.is_file():
        raise RuntimeError("pinned model snapshot is missing model.safetensors")
    model_size, model_digest = _sha256_file(model_file)
    hub_elapsed = time.perf_counter() - hub_started

    vllm_version = importlib.metadata.version("vllm")
    torch_version = importlib.metadata.version("torch")
    if _base_version(vllm_version) != str(spec["expected_vllm_version"]):
        raise RuntimeError(
            f"vLLM version mismatch: observed={vllm_version!r} expected={spec['expected_vllm_version']!r}"
        )
    if _base_version(torch_version) != str(spec["expected_torch_version"]):
        raise RuntimeError(
            f"PyTorch version mismatch: observed={torch_version!r} expected={spec['expected_torch_version']!r}"
        )

    native_module = importlib.import_module("vllm._C")
    native_module_file = str(getattr(native_module, "__file__", "") or "")
    if not native_module_file.endswith((".so", ".pyd")):
        raise RuntimeError(f"vllm._C is not a native extension: {native_module_file!r}")

    import torch
    from vllm import LLM, SamplingParams
    from vllm.platforms import current_platform

    device_type = str(getattr(current_platform, "device_type", "") or "")
    if device_type != "cpu":
        raise RuntimeError(f"vLLM selected {device_type!r}, not the CPU platform")

    prompt = str(inference["prompt"])
    sampling = SamplingParams(
        max_tokens=int(inference["max_tokens"]),
        temperature=float(inference["temperature"]),
        seed=int(inference["seed"]),
    )

    engine_started = time.perf_counter()
    llm = LLM(
        model=str(snapshot_path),
        tokenizer=str(snapshot_path),
        trust_remote_code=bool(model_contract["trust_remote_code"]),
        dtype=str(inference["dtype"]),
        max_model_len=int(inference["max_model_len"]),
        enforce_eager=True,
        seed=int(inference["seed"]),
        max_num_seqs=1,
        max_num_batched_tokens=int(inference["max_model_len"]),
        generation_config="vllm",
        device="cpu",
    )
    engine_ready_elapsed = time.perf_counter() - engine_started

    generation_started = time.perf_counter()
    outputs = llm.generate([prompt], sampling, use_tqdm=False)
    generation_elapsed = time.perf_counter() - generation_started
    if len(outputs) != 1 or not outputs[0].outputs:
        raise RuntimeError("vLLM returned no completion")
    completion = outputs[0].outputs[0]
    token_ids = [int(token) for token in completion.token_ids]
    if not token_ids:
        raise RuntimeError("vLLM executed but generated zero output tokens")

    proof: dict[str, Any] = {
        "schema": "a11oy.factory.runtime-execution/v1",
        "ok": True,
        "decision": "ALLOW",
        "executed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": str(spec["assurance"]["scope"]),
        "target": spec["target"],
        "runtime_execution_verified": True,
        "production_runtime_certified": False,
        "runtime": {
            "component": wheel["component"],
            "vllm_version": vllm_version,
            "torch_version": torch_version,
            "vllm_platform": device_type,
            "native_extension": native_module_file,
            "wheel_sha256": wheel["sha256"],
            "wheel_size": wheel["size"],
            "origin_host": wheel["origin_host"],
            "final_host": wheel["final_host"],
            "materialization_receipt_hash": wheel["materialization_receipt_hash"],
            "lock_digest": wheel["lock_digest"],
        },
        "model": {
            "id": model_id,
            "revision": observed_revision,
            "license": observed_license,
            "snapshot_path_name": snapshot_path.name,
            "model_file": model_file.name,
            "model_file_size": model_size,
            "model_file_sha256": model_digest,
            "trust_remote_code": False,
        },
        "inference": {
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "requested_max_tokens": int(inference["max_tokens"]),
            "generated_token_count": len(token_ids),
            "generated_token_ids": token_ids,
            "generated_text": str(completion.text),
            "finish_reason": getattr(completion, "finish_reason", None),
            "seed": int(inference["seed"]),
            "dtype": str(inference["dtype"]),
            "max_model_len": int(inference["max_model_len"]),
        },
        "host": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "torch_threads": torch.get_num_threads(),
            "vllm_target_device": os.environ.get("VLLM_TARGET_DEVICE"),
            "vllm_cpu_kvcache_space_gib": os.environ.get("VLLM_CPU_KVCACHE_SPACE"),
            "vllm_cpu_omp_threads_bind": os.environ.get("VLLM_CPU_OMP_THREADS_BIND"),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "ld_preload": os.environ.get("LD_PRELOAD"),
        },
        "timing_seconds": {
            "model_snapshot": round(hub_elapsed, 6),
            "engine_initialization": round(engine_ready_elapsed, 6),
            "generation": round(generation_elapsed, 6),
        },
        "assurance": {
            "satisfied": list(spec["assurance"]["required"]),
            "signing": "UNSIGNED-honest",
            "note": (
                "This proves one pinned model generated tokens through the pinned native vLLM CPU wheel "
                "on one GitHub-hosted AMD64 runner. It is not accelerator-wide or production certification."
            ),
        },
    }
    proof["proof_sha256"] = _canonical_digest(proof)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    shutdown = getattr(getattr(llm, "llm_engine", None), "shutdown", None)
    if callable(shutdown):
        shutdown()
    return proof


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--materialization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proof = execute(args.spec, args.materialization, args.output)
    print(json.dumps(proof, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
