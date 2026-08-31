#!/usr/bin/env python3
"""Emit a machine-verifiable receipt after cosign keyless verification succeeds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from a11oy_factory.assurance import AssuranceError, digest_json
from a11oy_factory.signed_promotion import (
    SIGSTORE_PROOF_SCHEMA,
    canonical_bytes,
    validate_signing_subject,
)


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


def _contains_transparency_material(value: Any) -> bool:
    if isinstance(value, Mapping):
        keys = {str(key).lower() for key in value}
        if keys & {
            "rekorbundle",
            "tlogentries",
            "logindex",
            "integratedtime",
            "inclusionpromise",
            "inclusionproof",
        }:
            return True
        return any(_contains_transparency_material(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_transparency_material(item) for item in value)
    return False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--verified-marker", type=Path, required=True)
    parser.add_argument("--cosign-binary", type=Path, required=True)
    parser.add_argument("--cosign-version-file", type=Path, required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.verified_marker.is_file():
        raise AssuranceError(
            "COSIGN_VERIFICATION_MISSING",
            "The cosign verification success marker is absent",
        )
    subject = _read(args.subject)
    validate_signing_subject(subject)
    bundle = _read(args.bundle)
    transparency = _contains_transparency_material(bundle)
    if not transparency:
        raise AssuranceError(
            "TRANSPARENCY_MATERIAL_MISSING",
            "The Sigstore bundle does not contain transparency-log material",
        )
    if args.issuer != "https://token.actions.githubusercontent.com":
        raise AssuranceError("OIDC_ISSUER_INVALID", "Issuer must be GitHub Actions")
    if not args.identity.endswith("@refs/heads/main"):
        raise AssuranceError("CERTIFICATE_IDENTITY_INVALID", "Identity must bind the main branch")

    body: dict[str, Any] = {
        "schema": SIGSTORE_PROOF_SCHEMA,
        "verified": True,
        "signer": "SIGSTORE-keyless",
        "certificate_identity": args.identity,
        "certificate_oidc_issuer": args.issuer,
        "subject_sha256": hashlib.sha256(canonical_bytes(subject)).hexdigest(),
        "subject_proof_sha256": subject["proof_sha256"],
        "bundle_sha256": _sha256(args.bundle),
        "cosign_binary_sha256": _sha256(args.cosign_binary),
        "cosign_version": args.cosign_version_file.read_text(encoding="utf-8").strip(),
        "transparency_log_verified": True,
        "transparency_material_embedded": transparency,
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "workflow": os.environ.get("GITHUB_WORKFLOW"),
        "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "commit_sha": os.environ.get("GITHUB_SHA"),
        "verification": {
            "method": "cosign verify-blob",
            "certificate_identity_exact": True,
            "certificate_oidc_issuer_exact": True,
            "offline": False,
        },
        "honesty": {
            "signature_binds_subject_only": True,
            "signature_does_not_certify_runtime": True,
            "signature_does_not_clear_vulnerabilities": True,
        },
    }
    body["proof_sha256"] = digest_json(body)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssuranceError as exc:
        print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
        raise SystemExit(2)
