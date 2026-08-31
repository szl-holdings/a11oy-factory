"""Finalize an assurance verdict only from verified cryptographic evidence."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping

from .assurance import ASSURANCE_VERDICT_SCHEMA, AssuranceError, digest_json, verify_verdict

SIGNING_SUBJECT_SCHEMA = "a11oy.factory.signing-subject/v1"
SIGSTORE_PROOF_SCHEMA = "a11oy.factory.sigstore-proof/v1"
SIGNED_PROMOTION_SCHEMA = "a11oy.factory.signed-promotion-verdict/v1"
SIGNATURE_ISSUE_CODE = "CRYPTOGRAPHIC_SIGNATURE_REQUIRED"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_embedded_digest(value: Mapping[str, Any], field: str = "proof_sha256") -> bool:
    supplied = value.get(field)
    if not isinstance(supplied, str) or len(supplied) != 64:
        return False
    body = deepcopy(dict(value))
    body.pop(field, None)
    return supplied == digest_json(body)


def validate_signing_subject(subject: Mapping[str, Any]) -> None:
    issues: list[str] = []
    if subject.get("schema") != SIGNING_SUBJECT_SCHEMA:
        issues.append(f"schema must equal {SIGNING_SUBJECT_SCHEMA}")
    for key in (
        "repository",
        "commit_sha",
        "scan_sha256",
        "runtime_proof_sha256",
        "distribution_lock_sha256",
        "initial_stable_verdict_sha256",
    ):
        value = subject.get(key)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"{key} must be a non-empty string")
    for key in (
        "scan_sha256",
        "runtime_proof_sha256",
        "distribution_lock_sha256",
        "initial_stable_verdict_sha256",
    ):
        value = subject.get(key)
        if isinstance(value, str) and (len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value)):
            issues.append(f"{key} must be lowercase SHA-256 hex")
    if not verify_embedded_digest(subject):
        issues.append("proof_sha256 does not verify")
    if issues:
        raise AssuranceError(
            "INVALID_SIGNING_SUBJECT",
            "Signing subject is invalid.",
            details={"issues": issues},
        )


def validate_sigstore_proof(proof: Mapping[str, Any], subject: Mapping[str, Any]) -> None:
    issues: list[str] = []
    if proof.get("schema") != SIGSTORE_PROOF_SCHEMA:
        issues.append(f"schema must equal {SIGSTORE_PROOF_SCHEMA}")
    if proof.get("verified") is not True:
        issues.append("verified must be true")
    if proof.get("signer") != "SIGSTORE-keyless":
        issues.append("signer must equal SIGSTORE-keyless")
    if proof.get("certificate_oidc_issuer") != "https://token.actions.githubusercontent.com":
        issues.append("certificate_oidc_issuer must be GitHub Actions")
    identity = proof.get("certificate_identity")
    if not isinstance(identity, str) or "/.github/workflows/" not in identity or not identity.endswith("@refs/heads/main"):
        issues.append("certificate_identity must bind a main-branch GitHub workflow")
    subject_sha256 = proof.get("subject_sha256")
    if subject_sha256 != sha256_bytes(canonical_bytes(subject)):
        issues.append("subject_sha256 does not bind the supplied signing subject")
    if proof.get("subject_proof_sha256") != subject.get("proof_sha256"):
        issues.append("subject_proof_sha256 does not match")
    bundle_sha256 = proof.get("bundle_sha256")
    if not isinstance(bundle_sha256, str) or len(bundle_sha256) != 64:
        issues.append("bundle_sha256 must be SHA-256 hex")
    if proof.get("transparency_log_verified") is not True:
        issues.append("transparency_log_verified must be true")
    if not verify_embedded_digest(proof):
        issues.append("proof_sha256 does not verify")
    if issues:
        raise AssuranceError(
            "INVALID_SIGSTORE_PROOF",
            "Sigstore verification proof is invalid.",
            details={"issues": issues},
        )


def finalize_stable_verdict(
    initial_verdict: Mapping[str, Any],
    subject: Mapping[str, Any],
    sigstore_proof: Mapping[str, Any],
) -> dict[str, Any]:
    """Remove only the signature blocker that the verified proof satisfies."""

    if initial_verdict.get("schema") != ASSURANCE_VERDICT_SCHEMA or not verify_verdict(initial_verdict):
        raise AssuranceError("INVALID_INITIAL_VERDICT", "Initial assurance verdict is invalid")
    if initial_verdict.get("channel") != "stable":
        raise AssuranceError("WRONG_CHANNEL", "Only a stable verdict can be cryptographically finalized")
    validate_signing_subject(subject)
    validate_sigstore_proof(sigstore_proof, subject)

    if subject.get("scan_sha256") != initial_verdict.get("scan_sha256"):
        raise AssuranceError("SCAN_BINDING_MISMATCH", "Signing subject does not bind the stable verdict scan")
    if subject.get("runtime_proof_sha256") != initial_verdict.get("runtime_proof_sha256"):
        raise AssuranceError("RUNTIME_BINDING_MISMATCH", "Signing subject does not bind the runtime proof")
    if subject.get("initial_stable_verdict_sha256") != initial_verdict.get("proof_sha256"):
        raise AssuranceError("VERDICT_BINDING_MISMATCH", "Signing subject does not bind the initial stable verdict")

    initial_issues = initial_verdict.get("issues")
    if not isinstance(initial_issues, list):
        raise AssuranceError("INVALID_INITIAL_ISSUES", "Initial stable verdict issues must be an array")
    signature_issues = [
        issue
        for issue in initial_issues
        if isinstance(issue, Mapping) and issue.get("code") == SIGNATURE_ISSUE_CODE
    ]
    if len(signature_issues) != 1:
        raise AssuranceError(
            "SIGNATURE_BLOCKER_AMBIGUOUS",
            "Initial stable verdict must contain exactly one signature blocker",
            details={"count": len(signature_issues)},
        )
    remaining = [
        deepcopy(issue)
        for issue in initial_issues
        if not (isinstance(issue, Mapping) and issue.get("code") == SIGNATURE_ISSUE_CODE)
    ]
    body: dict[str, Any] = {
        "schema": SIGNED_PROMOTION_SCHEMA,
        "ok": not remaining,
        "decision": "ALLOW" if not remaining else "BLOCKED",
        "channel": "stable",
        "policy_id": initial_verdict.get("policy_id"),
        "initial_verdict_sha256": initial_verdict.get("proof_sha256"),
        "signing_subject_sha256": subject.get("proof_sha256"),
        "sigstore_proof_sha256": sigstore_proof.get("proof_sha256"),
        "scan_sha256": initial_verdict.get("scan_sha256"),
        "runtime_proof_sha256": initial_verdict.get("runtime_proof_sha256"),
        "runtime_execution_verified": initial_verdict.get("runtime_execution_verified") is True,
        "production_runtime_certified": initial_verdict.get("production_runtime_certified") is True,
        "signer": "SIGSTORE-keyless",
        "cryptographic_signature": True,
        "certificate_identity": sigstore_proof.get("certificate_identity"),
        "certificate_oidc_issuer": sigstore_proof.get("certificate_oidc_issuer"),
        "transparency_log_verified": True,
        "resolved_issue": deepcopy(signature_issues[0]),
        "issues": remaining,
        "counts": {
            "initial_issues": len(initial_issues),
            "resolved_signature_issues": 1,
            "remaining_issues": len(remaining),
        },
        "honesty": {
            "signature_verifies_the_bound_subject": True,
            "signature_does_not_erase_other_policy_failures": True,
            "scoped_execution_is_not_production_certification": True,
        },
    }
    body["proof_sha256"] = digest_json(body)
    return body


def verify_signed_promotion(verdict: Mapping[str, Any]) -> bool:
    return verdict.get("schema") == SIGNED_PROMOTION_SCHEMA and verify_embedded_digest(verdict)
