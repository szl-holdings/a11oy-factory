"""Supply-chain assurance and promotion policy for A11oy Factory.

The module evaluates measured evidence. It never converts artifact integrity into
runtime safety, a vulnerability query into absence of risk, or an unsigned hash
into a cryptographic signature.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from typing import Any, Mapping

ASSURANCE_SCAN_SCHEMA = "a11oy.factory.assurance-scan/v1"
ASSURANCE_POLICY_SCHEMA = "a11oy.factory.assurance-policy/v1"
ASSURANCE_VERDICT_SCHEMA = "a11oy.factory.assurance-verdict/v1"
OSV_BATCH_ENDPOINT = "https://api.osv.dev/v1/querybatch"

SEVERITY_ORDER = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
    "UNKNOWN": 5,
}
LICENSE_ORDER = {
    "UNKNOWN": 0,
    "EVIDENCE_ONLY": 1,
    "DECLARED": 2,
    "STRUCTURED": 3,
}

_NAME_RE = re.compile(r"[-_.]+")
_CVSS_PAIR_RE = re.compile(r"([A-Z]{1,3}):([A-Z])")


class AssuranceError(ValueError):
    """Structured assurance error."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "decision": "BLOCKED",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def canonical_name(name: str) -> str:
    return _NAME_RE.sub("-", str(name).strip()).lower()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _round_up_tenth(value: float) -> float:
    return math.ceil((value - 1e-10) * 10.0) / 10.0


def cvss3_base_score(vector: str) -> float | None:
    """Calculate a CVSS v3.0/v3.1 base score from a complete base vector."""

    text = str(vector or "").strip().upper()
    if not text.startswith(("CVSS:3.0/", "CVSS:3.1/")):
        return None
    metrics = dict(_CVSS_PAIR_RE.findall(text))
    required = {"AV", "AC", "PR", "UI", "S", "C", "I", "A"}
    if not required.issubset(metrics):
        return None

    av = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}.get(metrics["AV"])
    ac = {"L": 0.77, "H": 0.44}.get(metrics["AC"])
    ui = {"N": 0.85, "R": 0.62}.get(metrics["UI"])
    scope = metrics["S"]
    pr_table = (
        {"N": 0.85, "L": 0.68, "H": 0.50}
        if scope == "C"
        else {"N": 0.85, "L": 0.62, "H": 0.27}
    )
    pr = pr_table.get(metrics["PR"])
    cia_table = {"N": 0.0, "L": 0.22, "H": 0.56}
    confidentiality = cia_table.get(metrics["C"])
    integrity = cia_table.get(metrics["I"])
    availability = cia_table.get(metrics["A"])
    values = (av, ac, ui, pr, confidentiality, integrity, availability)
    if scope not in {"U", "C"} or any(value is None for value in values):
        return None

    impact_subscore = 1 - (1 - confidentiality) * (1 - integrity) * (1 - availability)
    if scope == "U":
        impact = 6.42 * impact_subscore
    else:
        impact = 7.52 * (impact_subscore - 0.029) - 3.25 * ((impact_subscore - 0.02) ** 15)
    if impact <= 0:
        return 0.0
    exploitability = 8.22 * av * ac * pr * ui
    score = min(impact + exploitability, 10.0)
    if scope == "C":
        score = min(1.08 * (impact + exploitability), 10.0)
    return _round_up_tenth(score)


def score_to_severity(score: float | int | str | None) -> str:
    try:
        value = float(score)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "UNKNOWN"
    if value < 0 or value > 10:
        return "UNKNOWN"
    if value == 0:
        return "NONE"
    if value < 4.0:
        return "LOW"
    if value < 7.0:
        return "MEDIUM"
    if value < 9.0:
        return "HIGH"
    return "CRITICAL"


def normalize_severity(value: Any) -> str:
    text = str(value or "").strip().upper()
    aliases = {
        "MODERATE": "MEDIUM",
        "IMPORTANT": "HIGH",
        "SEVERE": "CRITICAL",
        "NEGLIGIBLE": "LOW",
    }
    text = aliases.get(text, text)
    return text if text in SEVERITY_ORDER else "UNKNOWN"


def vulnerability_severity(vulnerability: Mapping[str, Any]) -> dict[str, Any]:
    """Return an honest best available severity and its evidence source."""

    database_specific = vulnerability.get("database_specific")
    if isinstance(database_specific, Mapping):
        label = normalize_severity(database_specific.get("severity"))
        if label != "UNKNOWN":
            return {"label": label, "score": None, "source": "database_specific.severity"}

    ecosystem_specific = vulnerability.get("ecosystem_specific")
    if isinstance(ecosystem_specific, Mapping):
        label = normalize_severity(ecosystem_specific.get("severity"))
        if label != "UNKNOWN":
            return {"label": label, "score": None, "source": "ecosystem_specific.severity"}

    candidates: list[tuple[float, str]] = []
    raw = vulnerability.get("severity")
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            score = item.get("score")
            source = str(item.get("type") or "severity.score")
            numeric: float | None = None
            try:
                numeric = float(score)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                numeric = cvss3_base_score(str(score or ""))
            if numeric is not None:
                candidates.append((numeric, source))
    if candidates:
        score, source = max(candidates, key=lambda pair: pair[0])
        return {"label": score_to_severity(score), "score": score, "source": source}

    return {"label": "UNKNOWN", "score": None, "source": "unavailable"}


def license_status(package: Mapping[str, Any]) -> str:
    structured = str(package.get("license_expression") or "").strip()
    if structured and structured.upper() not in {"UNKNOWN", "NONE", "N/A"}:
        return "STRUCTURED"
    declared = str(package.get("license") or "").strip()
    classifiers = package.get("license_classifiers")
    if declared and declared.upper() not in {"UNKNOWN", "NONE", "N/A"}:
        return "DECLARED"
    if isinstance(classifiers, list) and any(str(item).strip() for item in classifiers):
        return "DECLARED"
    files = package.get("license_files")
    if isinstance(files, list) and files:
        return "EVIDENCE_ONLY"
    return "UNKNOWN"


def validate_policy(policy: Mapping[str, Any]) -> None:
    issues: list[str] = []
    if policy.get("schema") != ASSURANCE_POLICY_SCHEMA:
        issues.append(f"schema must equal {ASSURANCE_POLICY_SCHEMA}")
    if not isinstance(policy.get("id"), str) or not str(policy.get("id")).strip():
        issues.append("id must be a non-empty string")
    blocked = policy.get("block_severities")
    if not isinstance(blocked, list) or any(normalize_severity(item) == "UNKNOWN" for item in blocked):
        issues.append("block_severities must contain known severity labels")
    minimum = str(policy.get("minimum_license_status") or "")
    if minimum not in LICENSE_ORDER:
        issues.append("minimum_license_status is invalid")
    for key in (
        "require_osv_complete",
        "block_unknown_severity",
        "require_runtime_execution",
        "require_production_runtime_certification",
        "require_cryptographic_signature",
        "require_download_hashes",
    ):
        if not isinstance(policy.get(key), bool):
            issues.append(f"{key} must be boolean")
    if issues:
        raise AssuranceError("INVALID_POLICY", "Assurance policy is invalid.", details={"issues": issues})


def validate_scan(scan: Mapping[str, Any]) -> None:
    issues: list[str] = []
    if scan.get("schema") != ASSURANCE_SCAN_SCHEMA:
        issues.append(f"schema must equal {ASSURANCE_SCAN_SCHEMA}")
    if not isinstance(scan.get("packages"), list):
        issues.append("packages must be an array")
    if not isinstance(scan.get("vulnerabilities"), list):
        issues.append("vulnerabilities must be an array")
    if not isinstance(scan.get("osv"), Mapping):
        issues.append("osv must be an object")
    if issues:
        raise AssuranceError("INVALID_SCAN", "Assurance scan is invalid.", details={"issues": issues})


def evaluate_assurance(
    scan: Mapping[str, Any],
    runtime_proof: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate a channel without mutating or overstating the supplied evidence."""

    validate_scan(scan)
    validate_policy(policy)
    issues: list[dict[str, Any]] = []

    osv = scan.get("osv") if isinstance(scan.get("osv"), Mapping) else {}
    if policy["require_osv_complete"] and osv.get("complete") is not True:
        issues.append({"code": "OSV_INCOMPLETE", "message": "OSV batch evidence is incomplete."})

    if policy["require_runtime_execution"] and runtime_proof.get("runtime_execution_verified") is not True:
        issues.append({"code": "RUNTIME_NOT_EXECUTED", "message": "Scoped runtime execution proof is absent or false."})

    if (
        policy["require_production_runtime_certification"]
        and runtime_proof.get("production_runtime_certified") is not True
    ):
        issues.append(
            {
                "code": "PRODUCTION_RUNTIME_NOT_CERTIFIED",
                "message": "Production runtime certification is required and is not present.",
            }
        )

    signer = str(runtime_proof.get("signer") or runtime_proof.get("signing") or "UNSIGNED-honest")
    cryptographic = signer not in {"", "UNSIGNED", "UNSIGNED-honest", "UNAVAILABLE", "None"}
    if policy["require_cryptographic_signature"] and not cryptographic:
        issues.append(
            {
                "code": "CRYPTOGRAPHIC_SIGNATURE_REQUIRED",
                "message": "A tamper-evident hash is not a production cryptographic signature.",
                "observed": signer,
            }
        )

    blocked_severities = {normalize_severity(item) for item in policy["block_severities"]}
    blocked_vulnerabilities: list[dict[str, Any]] = []
    unknown_vulnerabilities: list[dict[str, Any]] = []
    vulnerabilities = scan.get("vulnerabilities")
    if isinstance(vulnerabilities, list):
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, Mapping):
                continue
            label = normalize_severity(vulnerability.get("severity"))
            row = {
                "id": vulnerability.get("id"),
                "package": vulnerability.get("package"),
                "version": vulnerability.get("version"),
                "severity": label,
                "summary": vulnerability.get("summary"),
            }
            if label in blocked_severities:
                blocked_vulnerabilities.append(row)
            if label == "UNKNOWN":
                unknown_vulnerabilities.append(row)
    if blocked_vulnerabilities:
        issues.append(
            {
                "code": "BLOCKED_VULNERABILITIES",
                "message": "One or more queried package versions matched blocked vulnerability severities.",
                "count": len(blocked_vulnerabilities),
                "vulnerabilities": blocked_vulnerabilities,
            }
        )
    if policy["block_unknown_severity"] and unknown_vulnerabilities:
        issues.append(
            {
                "code": "UNKNOWN_VULNERABILITY_SEVERITY",
                "message": "Vulnerabilities without severity are blocked by policy.",
                "count": len(unknown_vulnerabilities),
                "vulnerabilities": unknown_vulnerabilities,
            }
        )

    minimum_license = str(policy["minimum_license_status"])
    minimum_rank = LICENSE_ORDER[minimum_license]
    deficient_licenses: list[dict[str, Any]] = []
    missing_hashes: list[str] = []
    packages = scan.get("packages")
    if isinstance(packages, list):
        for package in packages:
            if not isinstance(package, Mapping):
                continue
            observed_license = license_status(package)
            if LICENSE_ORDER[observed_license] < minimum_rank:
                deficient_licenses.append(
                    {
                        "name": package.get("name"),
                        "version": package.get("version"),
                        "status": observed_license,
                    }
                )
            if policy["require_download_hashes"]:
                hashes = package.get("download_hashes")
                if not isinstance(hashes, Mapping) or not hashes.get("sha256"):
                    missing_hashes.append(str(package.get("name") or "<unknown>"))
    if deficient_licenses:
        issues.append(
            {
                "code": "LICENSE_EVIDENCE_BELOW_POLICY",
                "message": f"Packages do not meet minimum license status {minimum_license}.",
                "count": len(deficient_licenses),
                "packages": deficient_licenses,
            }
        )
    if missing_hashes:
        issues.append(
            {
                "code": "DOWNLOAD_HASH_REQUIRED",
                "message": "Resolved packages are missing SHA-256 download evidence.",
                "count": len(missing_hashes),
                "packages": sorted(missing_hashes),
            }
        )

    counts = scan.get("counts") if isinstance(scan.get("counts"), Mapping) else {}
    body: dict[str, Any] = {
        "schema": ASSURANCE_VERDICT_SCHEMA,
        "ok": not issues,
        "decision": "ALLOW" if not issues else "BLOCKED",
        "channel": policy.get("channel"),
        "policy_id": policy.get("id"),
        "scan_sha256": str(scan.get("proof_sha256") or digest_json(scan)),
        "runtime_proof_sha256": str(runtime_proof.get("proof_sha256") or digest_json(runtime_proof)),
        "runtime_execution_verified": runtime_proof.get("runtime_execution_verified") is True,
        "production_runtime_certified": runtime_proof.get("production_runtime_certified") is True,
        "signer": signer,
        "cryptographic_signature": cryptographic,
        "counts": {
            "packages": int(counts.get("packages") or len(packages or [])),
            "vulnerabilities": int(counts.get("vulnerabilities") or len(vulnerabilities or [])),
            "blocked_vulnerabilities": len(blocked_vulnerabilities),
            "unknown_severity_vulnerabilities": len(unknown_vulnerabilities),
            "license_deficiencies": len(deficient_licenses),
            "missing_download_hashes": len(missing_hashes),
            "issues": len(issues),
        },
        "issues": issues,
        "honesty": {
            "artifact_integrity_is_not_vulnerability_clearance": True,
            "scoped_execution_is_not_production_certification": True,
            "unsigned_hash_is_not_signature": True,
        },
    }
    body["proof_sha256"] = digest_json(body)
    return body


def verify_verdict(verdict: Mapping[str, Any]) -> bool:
    if verdict.get("schema") != ASSURANCE_VERDICT_SCHEMA:
        return False
    supplied = verdict.get("proof_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        return False
    body = deepcopy(dict(verdict))
    body.pop("proof_sha256", None)
    return supplied == digest_json(body)
