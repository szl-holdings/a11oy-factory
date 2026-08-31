"""Build plans, SBOMs, provenance, bundle output, and verification."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from pathlib import Path
from typing import Any, Mapping

from .distribution_common import (
    BUNDLE_BUILD_TYPE,
    IN_TOTO_STATEMENT,
    PLAN_SCHEMA,
    SLSA_PREDICATE,
    VERIFY_SCHEMA,
    FactoryError,
    _artifact_filename,
    _digest_prefixed,
    _atomic_write,
    _source_digest,
    _spdx_safe,
    _validate_lock_shape,
    canonical_bytes,
    digest_json,
)
from .distribution_resolver import resolve_distribution

def build_plan(lock: Mapping[str, Any]) -> dict[str, Any]:
    _validate_lock_shape(lock)
    steps: list[dict[str, Any]] = []
    for component in lock["components"]:
        source = component["source"]
        if source.get("type") in {"artifact", "oci"}:
            steps.append(
                {
                    "id": f"fetch:{component['id']}",
                    "component": component["id"],
                    "action": "fetch",
                    "uri": source["uri"],
                    "digest": source["digest"],
                    "size": source["size"],
                    "output": f"artifacts/{_artifact_filename(component)}",
                    "network": True,
                    "execute_by_default": False,
                }
            )
        elif source.get("type") == "git":
            steps.append(
                {
                    "id": f"checkout:{component['id']}",
                    "component": component["id"],
                    "action": "checkout",
                    "uri": source["uri"],
                    "revision": source["revision"],
                    "output": f"sources/{component['id']}",
                    "network": True,
                    "execute_by_default": False,
                }
            )
        for index, build_step in enumerate((component.get("build") or {}).get("steps") or []):
            steps.append(
                {
                    "id": f"build:{component['id']}:{index + 1}",
                    "component": component["id"],
                    "action": "exec",
                    "name": build_step["name"],
                    "argv": list(build_step["argv"]),
                    "cwd": build_step.get("cwd", "."),
                    "network": bool((component.get("build") or {}).get("network")),
                    "execute_by_default": False,
                }
            )
    steps.append(
        {
            "id": "verify:bundle",
            "component": "<distribution>",
            "action": "verify",
            "lock_digest": lock["lock_digest"],
            "network": False,
            "execute_by_default": True,
        }
    )
    body = {
        "schema": PLAN_SCHEMA,
        "profile": lock["profile"],
        "source_date_epoch": lock["source_date_epoch"],
        "lock_digest": lock["lock_digest"],
        "default_mode": "PLAN_ONLY",
        "steps": steps,
    }
    return {**body, "plan_digest": _digest_prefixed(body)}

def generate_spdx(lock: Mapping[str, Any]) -> dict[str, Any]:
    _validate_lock_shape(lock)
    lock_hex = str(lock["lock_digest"]).split(":", 1)[1]
    packages: list[dict[str, Any]] = []
    for component in lock["components"]:
        source = component["source"]
        package: dict[str, Any] = {
            "SPDXID": f"SPDXRef-Package-{_spdx_safe(component['id'])}",
            "name": component["id"],
            "versionInfo": component["version"],
            "supplier": f"Organization: {component['supplier']}",
            "downloadLocation": source["uri"],
            "filesAnalyzed": False,
            "licenseConcluded": component["license"],
            "licenseDeclared": component["license"],
            "copyrightText": "NOASSERTION",
            "summary": component["description"],
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:generic/{urllib.parse.quote(component['id'])}@{urllib.parse.quote(component['version'])}",
                }
            ],
        }
        source_hex = _source_digest(source)
        if source_hex:
            package["checksums"] = [{"algorithm": "SHA256", "checksumValue": source_hex}]
        packages.append(package)

    relationships: list[dict[str, Any]] = []
    for root in lock["profile"]["roots"]:
        relationships.append(
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": f"SPDXRef-Package-{_spdx_safe(root)}",
            }
        )
    for edge in lock["graph"]["edges"]:
        relationships.append(
            {
                "spdxElementId": f"SPDXRef-Package-{_spdx_safe(edge['from'])}",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": f"SPDXRef-Package-{_spdx_safe(edge['to'])}",
            }
        )
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"a11oy-factory-{lock['profile']['id']}",
        "documentNamespace": f"https://a-11-oy.com/factory/spdx/{lock_hex}",
        "creationInfo": {
            "created": lock["created"],
            "creators": ["Tool: a11oy-factory"],
            "licenseListVersion": "3.25",
        },
        "documentComment": "Integrity-locked distribution metadata. Runtime and vulnerability certification are separate gates.",
        "packages": packages,
        "relationships": sorted(
            relationships,
            key=lambda relation: (
                relation["spdxElementId"],
                relation["relationshipType"],
                relation["relatedSpdxElement"],
            ),
        ),
    }

def generate_provenance(lock: Mapping[str, Any]) -> dict[str, Any]:
    _validate_lock_shape(lock)
    lock_hex = str(lock["lock_digest"]).split(":", 1)[1]
    materials: list[dict[str, Any]] = []
    for component in lock["components"]:
        source = component["source"]
        material: dict[str, Any] = {"uri": source["uri"]}
        source_hex = _source_digest(source)
        if source_hex:
            material["digest"] = {"sha256": source_hex}
        elif source.get("type") == "git":
            material["digest"] = {"gitCommit": source["revision"]}
        materials.append(material)
    return {
        "_type": IN_TOTO_STATEMENT,
        "subject": [
            {
                "name": f"a11oy-factory/{lock['profile']['id']}/factory.lock.json",
                "digest": {"sha256": lock_hex},
            }
        ],
        "predicateType": SLSA_PREDICATE,
        "predicate": {
            "buildDefinition": {
                "buildType": BUNDLE_BUILD_TYPE,
                "externalParameters": {
                    "profile": lock["profile"],
                    "catalogDigest": lock["catalog_digest"],
                    "profileDigest": lock["profile_digest"],
                },
                "internalParameters": {
                    "mode": "PLAN_ONLY",
                    "runtimeCertified": False,
                },
                "resolvedDependencies": materials,
            },
            "runDetails": {
                "builder": {"id": "https://a-11-oy.com/factory/v1"},
                "metadata": {
                    "invocationId": lock["receipt"]["id"],
                    "startedOn": lock["created"],
                    "finishedOn": lock["created"],
                },
                "byproducts": [
                    {
                        "name": "a11oy-receipt",
                        "content": lock["receipt"],
                    }
                ],
            },
        },
    }

def verify_distribution(
    catalog: Mapping[str, Any],
    profile: Mapping[str, Any],
    lock: Mapping[str, Any],
    *,
    sbom: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, message: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "message": message})

    try:
        expected = resolve_distribution(catalog, profile, strict=False)
    except FactoryError as exc:
        return {
            "schema": VERIFY_SCHEMA,
            "ok": False,
            "decision": "BLOCKED",
            "checks": [{"name": "re-resolve", "ok": False, "message": exc.message}],
            "error": exc.as_dict()["error"],
        }

    check("catalog-digest", lock.get("catalog_digest") == expected["catalog_digest"], "Catalog digest matches." if lock.get("catalog_digest") == expected["catalog_digest"] else "Catalog digest mismatch.")
    check("profile-digest", lock.get("profile_digest") == expected["profile_digest"], "Profile digest matches." if lock.get("profile_digest") == expected["profile_digest"] else "Profile digest mismatch.")
    check("lock", canonical_bytes(lock) == canonical_bytes(expected), "Lock is reproducible." if canonical_bytes(lock) == canonical_bytes(expected) else "Lock differs from deterministic resolution.")

    lock_digest = str(lock.get("lock_digest") or "")
    expected_hex = str(expected["lock_digest"]).split(":", 1)[1]
    receipt = lock.get("receipt") if isinstance(lock.get("receipt"), dict) else {}
    receipt_without_hash = {key: value for key, value in receipt.items() if key != "hash"}
    check(
        "receipt-hash",
        receipt.get("hash") == digest_json(receipt_without_hash),
        "Receipt hash is valid." if receipt.get("hash") == digest_json(receipt_without_hash) else "Receipt hash mismatch.",
    )
    check(
        "receipt-subject",
        ((receipt.get("subject") or {}).get("digest") or {}).get("sha256") == expected_hex,
        "Receipt subject matches lock." if ((receipt.get("subject") or {}).get("digest") or {}).get("sha256") == expected_hex else "Receipt subject mismatch.",
    )

    if sbom is not None:
        expected_sbom = generate_spdx(expected)
        check("spdx", canonical_bytes(sbom) == canonical_bytes(expected_sbom), "SPDX SBOM matches." if canonical_bytes(sbom) == canonical_bytes(expected_sbom) else "SPDX SBOM mismatch.")
    if provenance is not None:
        expected_provenance = generate_provenance(expected)
        check(
            "provenance",
            canonical_bytes(provenance) == canonical_bytes(expected_provenance),
            "SLSA provenance matches." if canonical_bytes(provenance) == canonical_bytes(expected_provenance) else "SLSA provenance mismatch.",
        )

    ok = all(item["ok"] for item in checks)
    return {
        "schema": VERIFY_SCHEMA,
        "ok": ok,
        "decision": "ALLOW" if ok else "BLOCKED",
        "profile": expected["profile"]["id"],
        "lock_digest": lock_digest,
        "checks": checks,
        "note": "Verification proves metadata integrity and reproducibility, not runtime safety.",
    }

def write_bundle(
    catalog: Mapping[str, Any],
    profile: Mapping[str, Any],
    out_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    lock = resolve_distribution(catalog, profile)
    plan = build_plan(lock)
    sbom = generate_spdx(lock)
    provenance = generate_provenance(lock)
    verification = verify_distribution(catalog, profile, lock, sbom=sbom, provenance=provenance)
    documents = {
        "factory.lock.json": lock,
        "factory.plan.json": plan,
        "factory.spdx.json": sbom,
        "factory.provenance.json": provenance,
        "factory.verification.json": verification,
    }
    sums: list[str] = []
    for filename, document in documents.items():
        payload = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        _atomic_write(destination / filename, payload.encode("utf-8"))
        sums.append(f"{hashlib.sha256(payload.encode('utf-8')).hexdigest()}  {filename}")
    sums_payload = "\n".join(sorted(sums)) + "\n"
    _atomic_write(destination / "SHA256SUMS", sums_payload.encode("utf-8"))
    return {
        "ok": True,
        "decision": "ALLOW",
        "profile": profile["id"],
        "out_dir": str(destination),
        "lock_digest": lock["lock_digest"],
        "files": sorted([*documents.keys(), "SHA256SUMS"]),
        "verification": verification,
    }
