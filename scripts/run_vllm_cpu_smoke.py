#!/usr/bin/env python3
"""Execute a pinned vLLM CPU inference and emit a scoped runtime proof."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _event(name: str, **fields: Any) -> None:
    """Emit a flushed, machine-readable progress breadcrumb."""

    print(json.dumps({"event": name, **fields}, sort_keys=True, default=str), flush=True)


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


def _model_license(info: Any) -> str | None:
    card_data = getattr(info, "card_data", None)
    if card_data is None:
        return None
    if isinstance(card_data, dict):
        value = card_data.get("license")
    else:
        value = getattr(card_data, "license", None)
    return str(value) if value else None


def _verified_record(record: dict[str, Any], component_id: str) -> dict[str, Any]:
    if record.get("component") != component_id:
        raise RuntimeError(f"materialized component does not match {component_id!r}")
    if record.get("status") not in {"DOWNLOADED_VERIFIED", "REUSED_VERIFIED"}:
        raise RuntimeError(f"component {component_id!r} bytes were not verified")
    wheel_path = Path(str(record.get("path") or ""))
    if not wheel_path.is_file():
        raise RuntimeError(f"verified wheel is missing: {wheel_path}")
    wheel_size, wheel_digest = _sha256_file(wheel_path)
    if wheel_size != int(record.get("size", -1)) or wheel_digest != record.get("sha256"):
        raise RuntimeError(f"component {component_id!r} changed after materialization")
    return {
        "component": component_id,
        "path": str(wheel_path),
        "size": wheel_size,
        "sha256": wheel_digest,
        "origin_host": record.get("origin_host"),
        "final_host": record.get("final_host"),
    }


def _validate_contract(spec: dict[str, Any], materialization: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema") != "a11oy.factory.runtime-smoke/v1":
        raise RuntimeError("unsupported runtime smoke schema")
    if spec.get("target") != "linux-amd64-cpu":
        raise RuntimeError("this executor only verifies the linux-amd64-cpu smoke target")
    if materialization.get("ok") is not True or materialization.get("decision") != "ALLOW":
        raise RuntimeError("runtime wheel materialization was not ALLOW")

    runtime_component = str(spec.get("runtime_component") or "")
    torch_component = str(spec.get("torch_component") or "")
    required = {runtime_component, torch_component}
    if "" in required or len(required) != 2:
        raise RuntimeError("runtime contract must name distinct vLLM and PyTorch components")

    records = materialization.get("artifacts")
    if not isinstance(records, list):
        raise RuntimeError("runtime materialization is missing artifact records")
    by_component = {
        str(record.get("component")): record
        for record in records
        if isinstance(record, dict) and record.get("component")
    }
    if set(by_component) != required:
        raise RuntimeError(
            f"runtime smoke requires exactly {sorted(required)!r}; observed {sorted(by_component)!r}"
        )

    return {
        "vllm": _verified_record(by_component[runtime_component], runtime_component),
        "torch": _verified_record(by_component[torch_component], torch_component),
        "materialization_receipt_hash": materialization.get("receipt_hash"),
        "lock_digest": materialization.get("lock_digest"),
    }


def _cpu_feature(torch_module: Any, name: str) -> bool:
    feature = getattr(getattr(torch_module, "cpu", None), name, None)
    if not callable(feature):
        return False
    try:
        return bool(feature())
    except Exception as exc:
        raise RuntimeError(f"unable to evaluate torch.cpu.{name}(): {exc}") from exc


def _select_cpu_native_variant(torch_module: Any, machine: str | None = None) -> str:
    """Mirror vLLM's x86 CPU extension selection without importing a DSO."""

    normalized = (machine or platform.machine()).strip().lower()
    if normalized not in {"x86_64", "amd64"}:
        return "_C"
    if _cpu_feature(torch_module, "_is_avx512_supported"):
        if _cpu_feature(torch_module, "_is_avx512_bf16_supported"):
            return "_C"
        return "_C_AVX512"
    return "_C_AVX2"


def _load_cpu_native_kernels(torch_module: Any, current_platform: Any) -> dict[str, Any]:
    """Let vLLM perform its own ISA dispatch, then prove CPU ops registered."""

    machine = platform.machine().strip().lower()
    selected_variant = _select_cpu_native_variant(torch_module, machine)
    selected_module = f"vllm.{selected_variant}"
    selected_spec = importlib.util.find_spec(selected_module)
    selected_path = str(getattr(selected_spec, "origin", "") or "")
    if selected_spec is None or not selected_path.endswith((".so", ".pyd")):
        raise RuntimeError(
            f"selected vLLM CPU extension is missing or not native: {selected_module!r} {selected_path!r}"
        )

    features = {
        "machine": machine,
        "avx512": _cpu_feature(torch_module, "_is_avx512_supported"),
        "avx512_bf16": _cpu_feature(torch_module, "_is_avx512_bf16_supported"),
        "selected_variant": selected_variant,
        "selected_module": selected_module,
        "selected_path": selected_path,
    }
    _event("native_dispatch_selected", **features)

    # This module invokes current_platform.import_kernels(), which is the
    # upstream vLLM entry point that selects _C, _C_AVX512, or _C_AVX2. The
    # alternate ISA libraries intentionally export Torch ops under namespace
    # _C and may raise a caught PyInit-name ImportError after registration.
    from vllm.kernels import vllm_c as _native_bootstrap  # noqa: F401

    ops_namespace = getattr(torch_module.ops, "_C", None)
    registered_ops = [
        name
        for name in ("cpu_attn_has_isa", "cpu_attention_with_kv_cache", "placeholder_op")
        if ops_namespace is not None and hasattr(ops_namespace, name)
    ]
    if "cpu_attn_has_isa" not in registered_ops:
        raise RuntimeError(
            "vLLM selected a CPU extension but the expected torch.ops._C CPU kernels were not registered"
        )

    mapped = False
    maps_path = Path("/proc/self/maps")
    if maps_path.is_file():
        selected_name = Path(selected_path).name
        mapped = selected_name in maps_path.read_text(encoding="utf-8", errors="replace")

    result = {
        **features,
        "registered_ops": registered_ops,
        "selected_extension_mapped": mapped,
        "dispatch": "vllm.current_platform.import_kernels",
    }
    _event("native_dispatch_verified", **result)
    return result


def execute(spec_path: Path, materialization_path: Path, output_path: Path) -> dict[str, Any]:
    spec = _read_json(spec_path)
    materialization = _read_json(materialization_path)
    wheels = _validate_contract(spec, materialization)
    _event(
        "runtime_contract_verified",
        lock_digest=wheels["lock_digest"],
        runtime_component=wheels["vllm"]["component"],
        torch_component=wheels["torch"]["component"],
    )

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

    vllm_version = importlib.metadata.version("vllm")
    torch_version = importlib.metadata.version("torch")
    if vllm_version != str(spec["expected_vllm_version"]):
        raise RuntimeError(
            f"vLLM version mismatch: observed={vllm_version!r} expected={spec['expected_vllm_version']!r}"
        )
    if torch_version != str(spec["expected_torch_version"]):
        raise RuntimeError(
            f"PyTorch version mismatch: observed={torch_version!r} expected={spec['expected_torch_version']!r}"
        )
    _event("runtime_versions_verified", torch=torch_version, vllm=vllm_version)

    import torch
    from vllm.platforms import current_platform

    device_type = str(getattr(current_platform, "device_type", "") or "")
    if device_type != "cpu":
        raise RuntimeError(f"vLLM selected {device_type!r}, not the CPU platform")
    if torch.cuda.is_available():
        raise RuntimeError("the CPU proof runner unexpectedly exposed CUDA")

    native_dispatch = _load_cpu_native_kernels(torch, current_platform)

    from huggingface_hub import HfApi, snapshot_download

    _event("model_revision_resolving", model=model_id, revision=revision)
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
    _event(
        "model_snapshot_verified",
        model=model_id,
        revision=observed_revision,
        license=observed_license,
        model_file_sha256=model_digest,
        model_file_size=model_size,
    )

    from vllm import LLM, SamplingParams

    prompt = str(inference["prompt"])
    sampling = SamplingParams(
        max_tokens=int(inference["max_tokens"]),
        temperature=float(inference["temperature"]),
        seed=int(inference["seed"]),
    )

    _event(
        "engine_initializing",
        model=str(snapshot_path),
        dtype=str(inference["dtype"]),
        max_model_len=int(inference["max_model_len"]),
        native_variant=native_dispatch["selected_variant"],
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
        # Device selection comes from VLLM_TARGET_DEVICE=cpu (set above before
        # the vLLM import); the pinned vLLM removed the LLM(device=...) kwarg.
    )
    engine_ready_elapsed = time.perf_counter() - engine_started
    _event("engine_initialized", elapsed_seconds=round(engine_ready_elapsed, 6))

    _event("generation_started", requested_max_tokens=int(inference["max_tokens"]))
    generation_started = time.perf_counter()
    outputs = llm.generate([prompt], sampling, use_tqdm=False)
    generation_elapsed = time.perf_counter() - generation_started
    if len(outputs) != 1 or not outputs[0].outputs:
        raise RuntimeError("vLLM returned no completion")
    completion = outputs[0].outputs[0]
    token_ids = [int(token) for token in completion.token_ids]
    if not token_ids:
        raise RuntimeError("vLLM executed but generated zero output tokens")
    _event(
        "generation_verified",
        generated_token_count=len(token_ids),
        generated_token_ids=token_ids,
        elapsed_seconds=round(generation_elapsed, 6),
    )

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
            "vllm": {
                **{key: value for key, value in wheels["vllm"].items() if key != "path"},
                "installed_version": vllm_version,
                "platform": device_type,
                "native_dispatch": native_dispatch,
            },
            "torch": {
                **{key: value for key, value in wheels["torch"].items() if key != "path"},
                "installed_version": torch_version,
                "cuda_available": torch.cuda.is_available(),
            },
            "materialization_receipt_hash": wheels["materialization_receipt_hash"],
            "lock_digest": wheels["lock_digest"],
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
                "This proves one immutable PyTorch CPU wheel and one immutable native vLLM CPU wheel "
                "loaded one pinned Apache-2.0 model revision and generated tokens on one Linux AMD64 "
                "GitHub-hosted CPU runner. It is not accelerator-wide or production certification."
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
