#!/usr/bin/env python3
"""Evaluate runtime, vulnerability, license, and provenance evidence by channel."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from a11oy_factory.assurance import (
    ASSURANCE_SCAN_SCHEMA,
    ASSURANCE_VERDICT_SCHEMA,
    AssuranceError,
    digest_json,
    evaluate_assurance,
    validate_policy,
    validate_scan,
    verify_verdict,
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssuranceError("INVALID_JSON", f"{path} must contain a JSON object")
    return value


def _verify_embedded_digest(value: Mapping[str, Any], field: str = "proof_sha256") -> bool:
    supplied = value.get(field)
    if not isinstance(supplied, str) or len(supplied) != 64:
        return False
    body = deepcopy(dict(value))
    body.pop(field, None)
    return supplied == digest_json(body)


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--runtime-proof", type=Path, required=True)
    parser.add_argument("--policy", type=Path, action="append", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--require-channel", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    scan = _read(args.scan)
    runtime_proof = _read(args.runtime_proof)
    validate_scan(scan)
    if scan.get("schema") != ASSURANCE_SCAN_SCHEMA or not _verify_embedded_digest(scan):
        raise AssuranceError("SCAN_DIGEST_INVALID", "Assurance scan proof digest is invalid")
    if runtime_proof.get("runtime_execution_verified") is not True:
        raise AssuranceError("RUNTIME_PROOF_INVALID", "Runtime proof does not show executed inference")
    if not _verify_embedded_digest(runtime_proof):
        raise AssuranceError("RUNTIME_DIGEST_INVALID", "Runtime execution proof digest is invalid")

    verdicts: dict[str, dict[str, Any]] = {}
    for policy_path in args.policy:
        policy = _read(policy_path)
        validate_policy(policy)
        channel = str(policy["channel"])
        if channel in verdicts:
            raise AssuranceError("DUPLICATE_CHANNEL", f"Duplicate policy for channel {channel}")
        verdict = evaluate_assurance(scan, runtime_proof, policy)
        if verdict.get("schema") != ASSURANCE_VERDICT_SCHEMA or not verify_verdict(verdict):
            raise AssuranceError("VERDICT_DIGEST_INVALID", f"Generated {channel} verdict is invalid")
        verdicts[channel] = verdict
        _write(args.out_dir / f"{channel}-verdict.json", verdict)

    required = set(args.require_channel)
    missing = required - set(verdicts)
    if missing:
        raise AssuranceError("MISSING_REQUIRED_CHANNEL", "Required channel verdict is absent", details={"channels": sorted(missing)})

    summary: dict[str, Any] = {
        "schema": "a11oy.factory.assurance-summary/v1",
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scan_sha256": scan["proof_sha256"],
        "runtime_proof_sha256": runtime_proof["proof_sha256"],
        "runtime_execution_verified": True,
        "production_runtime_certified": runtime_proof.get("production_runtime_certified") is True,
        "channels": {
            channel: {
                "decision": verdict["decision"],
                "ok": verdict["ok"],
                "issues": verdict["counts"]["issues"],
                "blocked_vulnerabilities": verdict["counts"]["blocked_vulnerabilities"],
                "proof_sha256": verdict["proof_sha256"],
            }
            for channel, verdict in sorted(verdicts.items())
        },
        "honesty": {
            "workflow_success_means_evidence_generated": True,
            "blocked_channel_is_a_valid_fail_closed_result": True,
            "production_runtime_certified": False,
        },
    }
    summary["proof_sha256"] = digest_json(summary)
    _write(args.out_dir / "assurance-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))

    blocked_required = [
        channel
        for channel in required
        if verdicts[channel]["decision"] != "ALLOW"
    ]
    if blocked_required:
        print(
            json.dumps(
                {
                    "ok": False,
                    "decision": "BLOCKED",
                    "required_channels": blocked_required,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 3
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssuranceError as exc:
        print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
        raise SystemExit(2)
