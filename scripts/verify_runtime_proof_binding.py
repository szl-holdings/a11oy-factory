#!/usr/bin/env python3
"""Verify a runtime proof's exact source and caller-run artifact binding.

The binding is CI provenance, not a signature or production certification.
Expected values must come from the current workflow context and producer outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


BINDING_SCHEMA = "a11oy.factory.runtime-workflow-binding/v1"


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_invalid_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def verify_binding(
    proof_path: Path,
    binding_path: Path,
    *,
    source_sha: str,
    run_id: str,
    run_attempt: str,
    proof_file_sha256: str,
) -> dict[str, Any]:
    """Reject missing, stale, altered, unsuccessful, or overclaimed evidence."""
    if re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise ValueError("expected source SHA must be a complete lowercase Git SHA")
    if re.fullmatch(r"[0-9a-f]{64}", proof_file_sha256) is None:
        raise ValueError("expected proof file SHA-256 is absent or malformed")
    if any(re.fullmatch(r"[1-9][0-9]*", value) is None for value in (run_id, run_attempt)):
        raise ValueError("expected workflow run identity is absent or malformed")

    binding = _read_object(binding_path)
    expected = {
        "schema": BINDING_SCHEMA,
        "source_sha": source_sha,
        "workflow_run_id": run_id,
        "workflow_run_attempt": run_attempt,
        "proof_file_sha256": proof_file_sha256,
    }
    if binding != expected:
        raise ValueError("runtime proof binding does not match the exact source and caller run")
    if hashlib.sha256(proof_path.read_bytes()).hexdigest() != proof_file_sha256:
        raise ValueError("runtime proof file bytes do not match the producer output")

    proof = _read_object(proof_path)
    if (
        proof.get("schema") != "a11oy.factory.runtime-execution/v1"
        or proof.get("ok") is not True
        or proof.get("decision") != "ALLOW"
        or proof.get("runtime_execution_verified") is not True
        or proof.get("production_runtime_certified") is not False
    ):
        raise ValueError("runtime proof is unsuccessful or exceeds its scoped certification")
    supplied = proof.get("proof_sha256")
    body = {key: value for key, value in proof.items() if key != "proof_sha256"}
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    if supplied != hashlib.sha256(canonical).hexdigest():
        raise ValueError("runtime proof embedded digest is invalid")
    return binding


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-proof", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    parser.add_argument("--proof-file-sha256", required=True)
    args = parser.parse_args()
    binding = verify_binding(
        args.runtime_proof,
        args.binding,
        source_sha=args.source_sha,
        run_id=args.run_id,
        run_attempt=args.run_attempt,
        proof_file_sha256=args.proof_file_sha256,
    )
    print(json.dumps({"binding_verified": True, **binding}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
