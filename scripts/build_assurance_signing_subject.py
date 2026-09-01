#!/usr/bin/env python3
"""Build the canonical evidence subject that Sigstore signs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from a11oy_factory.assurance import AssuranceError, digest_json, verify_verdict
from a11oy_factory.signed_promotion import SIGNING_SUBJECT_SCHEMA, verify_embedded_digest


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssuranceError("INVALID_JSON", f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_embedded(value: Mapping[str, Any], label: str) -> str:
    if not verify_embedded_digest(value):
        raise AssuranceError("INVALID_EVIDENCE_DIGEST", f"{label} proof digest does not verify")
    return str(value["proof_sha256"])


def _distribution_lock_identity(lock: Mapping[str, Any]) -> str:
    """Return the canonical content identity emitted by supported lock schemas."""

    for field in ("lock_id", "lock_digest", "digest", "id"):
        value = lock.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise AssuranceError("LOCK_ID_MISSING", "Distribution lock has no content identity")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--runtime-proof", type=Path, required=True)
    parser.add_argument("--distribution-lock", type=Path, required=True)
    parser.add_argument("--stable-verdict", type=Path, required=True)
    parser.add_argument("--stable-policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    scan = _read(args.scan)
    runtime = _read(args.runtime_proof)
    stable = _read(args.stable_verdict)
    lock = _read(args.distribution_lock)
    policy = _read(args.stable_policy)

    scan_sha = _require_embedded(scan, "scan")
    runtime_sha = _require_embedded(runtime, "runtime")
    if not verify_verdict(stable) or stable.get("channel") != "stable":
        raise AssuranceError("INVALID_STABLE_VERDICT", "Initial stable verdict is invalid")
    if stable.get("scan_sha256") != scan_sha:
        raise AssuranceError("SCAN_BINDING_MISMATCH", "Stable verdict does not bind the supplied scan")
    if stable.get("runtime_proof_sha256") != runtime_sha:
        raise AssuranceError("RUNTIME_BINDING_MISMATCH", "Stable verdict does not bind the supplied runtime proof")
    if stable.get("cryptographic_signature") is not False:
        raise AssuranceError("ALREADY_SIGNED", "Initial stable verdict must still be unsigned")
    if policy.get("id") != stable.get("policy_id") or policy.get("channel") != "stable":
        raise AssuranceError("POLICY_BINDING_MISMATCH", "Stable policy does not match the verdict")
    lock_id = _distribution_lock_identity(lock)

    repository = os.environ.get("GITHUB_REPOSITORY", "szl-holdings/a11oy-factory")
    commit_sha = os.environ.get("GITHUB_SHA", "0" * 40)
    ref = os.environ.get("GITHUB_REF", "refs/heads/main")
    workflow_ref = os.environ.get(
        "GITHUB_WORKFLOW_REF",
        f"{repository}/.github/workflows/factory-keyless-signing.yml@{ref}",
    )
    body: dict[str, Any] = {
        "schema": SIGNING_SUBJECT_SCHEMA,
        "repository": repository,
        "commit_sha": commit_sha,
        "ref": ref,
        "workflow_ref": workflow_ref,
        "scan_sha256": scan_sha,
        "runtime_proof_sha256": runtime_sha,
        "distribution_lock_sha256": _sha256(args.distribution_lock),
        "distribution_lock_id": lock_id,
        "initial_stable_verdict_sha256": stable["proof_sha256"],
        "stable_policy_sha256": _sha256(args.stable_policy),
        "stable_policy_id": stable["policy_id"],
        "evidence_files": {
            "scan": args.scan.name,
            "runtime_proof": args.runtime_proof.name,
            "distribution_lock": args.distribution_lock.name,
            "stable_verdict": args.stable_verdict.name,
            "stable_policy": args.stable_policy.name,
        },
        "assurance": {
            "runtime_execution_verified": runtime.get("runtime_execution_verified") is True,
            "production_runtime_certified": runtime.get("production_runtime_certified") is True,
            "initial_stable_decision": stable.get("decision"),
            "signature_state_before_signing": "UNSIGNED-honest",
        },
    }
    body["proof_sha256"] = digest_json(body)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "proof_sha256": body["proof_sha256"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssuranceError as exc:
        print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
        raise SystemExit(2)
