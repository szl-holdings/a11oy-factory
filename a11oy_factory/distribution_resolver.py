"""Deterministic dependency resolution and fail-closed policy evaluation."""

from __future__ import annotations

import urllib.parse
from copy import deepcopy
from typing import Any, Iterable, Mapping

from .distribution_common import (
    GENESIS,
    LOCK_SCHEMA,
    RECEIPT_SCHEMA,
    FactoryError,
    _digest_prefixed,
    _immutable_source,
    _timestamp,
    digest_json,
    validate_catalog,
    validate_profile,
)

def _merged_policy(catalog: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    policy = deepcopy(catalog.get("policy_defaults") or {})
    policy.update(deepcopy(profile.get("policy") or {}))
    return policy

def _policy_findings(
    components: Iterable[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    allowed_licenses = set(policy.get("allowed_licenses") or [])
    denied_licenses = set(policy.get("denied_licenses") or [])
    allowed_hosts = set(policy.get("allowed_source_hosts") or [])
    required_evidence = set(policy.get("required_evidence_types") or [])
    permitted_vulnerability = set(policy.get("permitted_vulnerability_status") or ["VERIFIED"])
    require_immutable = bool(policy.get("require_immutable_sources", True))
    allow_network = bool(policy.get("allow_network_builds", False))
    max_artifact_bytes = int(policy.get("max_artifact_bytes", 0) or 0)

    def add(level: str, code: str, message: str, component_id: str) -> None:
        findings.append({"level": level, "code": code, "component": component_id, "message": message})

    component_list = list(components)
    max_components = int(policy.get("max_components", 256) or 256)
    if len(component_list) > max_components:
        add("BLOCK", "too_many_components", f"{len(component_list)} components exceeds maximum {max_components}.", "<profile>")

    for component in component_list:
        component_id = str(component["id"])
        license_id = str(component["license"])
        if license_id in denied_licenses:
            add("BLOCK", "denied_license", f"License {license_id} is denied.", component_id)
        elif allowed_licenses and license_id not in allowed_licenses:
            add("BLOCK", "license_not_allowed", f"License {license_id} is not in the allowlist.", component_id)
        else:
            add("PASS", "license_allowed", f"License {license_id} is allowed.", component_id)

        source = component["source"]
        if require_immutable and not _immutable_source(source):
            add("BLOCK", "mutable_source", "Source is not pinned by an immutable commit or sha256 digest.", component_id)
        else:
            add("PASS", "immutable_source", "Source is immutably pinned.", component_id)

        host = urllib.parse.urlparse(str(source["uri"])).hostname or ""
        if allowed_hosts and host not in allowed_hosts:
            add("BLOCK", "source_host_denied", f"Source host {host!r} is not allowed.", component_id)
        else:
            add("PASS", "source_host_allowed", f"Source host {host!r} is allowed.", component_id)

        if max_artifact_bytes and source.get("type") in {"artifact", "oci"}:
            size = int(source.get("size") or 0)
            if size > max_artifact_bytes:
                add("BLOCK", "artifact_too_large", f"Artifact size {size} exceeds maximum {max_artifact_bytes}.", component_id)

        build = component.get("build") or {}
        if bool(build.get("network")) and not allow_network:
            add("BLOCK", "network_build_denied", "Build requests network access.", component_id)
        else:
            add("PASS", "network_policy", "Build network policy is satisfied.", component_id)

        evidence_types = {
            str(item.get("type"))
            for item in component.get("evidence", [])
            if isinstance(item, dict) and isinstance(item.get("type"), str)
        }
        missing = sorted(required_evidence - evidence_types)
        if missing:
            add("BLOCK", "missing_evidence", f"Missing required evidence: {', '.join(missing)}.", component_id)
        else:
            add("PASS", "evidence_complete", "Required evidence is present.", component_id)

        vulnerability_status = str((component.get("vulnerability") or {}).get("status") or "UNVERIFIED")
        if vulnerability_status not in permitted_vulnerability:
            level = "BLOCK" if bool(policy.get("block_unpermitted_vulnerability_status", True)) else "WARN"
            add(level, "vulnerability_status", f"Vulnerability status {vulnerability_status} is not permitted.", component_id)
        elif vulnerability_status == "UNVERIFIED":
            add("WARN", "vulnerability_unverified", "Integrity is pinned, but vulnerability evidence is not current.", component_id)
        else:
            add("PASS", "vulnerability_status", f"Vulnerability status {vulnerability_status} is permitted.", component_id)

    return findings

def _index_components(catalog: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): deepcopy(item) for item in catalog["components"]}

def _resolve_order(
    component_index: Mapping[str, Mapping[str, Any]],
    roots: list[str],
    target: str,
) -> list[str]:
    visiting: list[str] = []
    visited: set[str] = set()
    order: list[str] = []

    def visit(component_id: str) -> None:
        if component_id in visited:
            return
        if component_id in visiting:
            cycle_start = visiting.index(component_id)
            cycle = visiting[cycle_start:] + [component_id]
            raise FactoryError("dependency_cycle", "Dependency graph contains a cycle.", details={"cycle": cycle})
        component = component_index.get(component_id)
        if component is None:
            raise FactoryError("missing_component", f"Unknown component {component_id!r}.")
        targets = component.get("targets") or []
        if target not in targets and "*" not in targets:
            raise FactoryError(
                "incompatible_target",
                f"Component {component_id!r} does not support target {target!r}.",
                details={"component_targets": targets},
            )
        visiting.append(component_id)
        for dependency in sorted(component.get("requires") or []):
            visit(str(dependency))
        visiting.pop()
        visited.add(component_id)
        order.append(component_id)

    for root in sorted(roots):
        visit(root)
    return order

def resolve_distribution(
    catalog: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    strict: bool = True,
) -> dict[str, Any]:
    """Resolve a profile into a deterministic, content-addressed lock."""

    validate_catalog(catalog)
    validate_profile(profile, catalog)
    component_index = _index_components(catalog)
    roots = list(profile["roots"])
    target_id = str(profile["target"])
    order = _resolve_order(component_index, roots, target_id)
    selected = [component_index[component_id] for component_id in order]
    policy = _merged_policy(catalog, profile)
    findings = _policy_findings(selected, policy)
    blockers = [finding for finding in findings if finding["level"] == "BLOCK"]
    warnings = [finding for finding in findings if finding["level"] == "WARN"]
    if strict and blockers:
        raise FactoryError(
            "policy_blocked",
            "Distribution policy blocked the profile.",
            details={"findings": findings, "blockers": len(blockers), "warnings": len(warnings)},
        )

    locked_components: list[dict[str, Any]] = []
    for component in selected:
        descriptor = deepcopy(component)
        locked_components.append(
            {
                "id": descriptor["id"],
                "version": descriptor["version"],
                "kind": descriptor["kind"],
                "license": descriptor["license"],
                "supplier": descriptor["supplier"],
                "description": descriptor["description"],
                "source": descriptor["source"],
                "requires": sorted(descriptor.get("requires") or []),
                "targets": sorted(descriptor["targets"]),
                "build": descriptor.get("build") or {"network": False, "steps": []},
                "evidence": descriptor.get("evidence") or [],
                "vulnerability": descriptor["vulnerability"],
                "descriptor_digest": _digest_prefixed(descriptor),
            }
        )

    epoch = int(profile["source_date_epoch"])
    edges = [
        {"from": component["id"], "to": dependency}
        for component in locked_components
        for dependency in component["requires"]
    ]
    target = deepcopy(catalog["targets"][target_id])
    policy_decision = "BLOCKED" if blockers else "ALLOW"
    lock_body: dict[str, Any] = {
        "schema": LOCK_SCHEMA,
        "factory": {
            "name": "A11oy Trusted AI Factory",
            "mode": "deterministic-metadata-distribution",
            "runtime_certified": False,
        },
        "profile": {
            "id": profile["id"],
            "channel": profile["channel"],
            "assurance": profile["assurance"],
            "roots": sorted(roots),
            "target": target_id,
            "target_spec": target,
        },
        "source_date_epoch": epoch,
        "created": _timestamp(epoch),
        "catalog_digest": _digest_prefixed(catalog),
        "profile_digest": _digest_prefixed(profile),
        "policy": {
            "decision": policy_decision,
            "blockers": len(blockers),
            "warnings": len(warnings),
            "findings": findings,
            "effective": policy,
        },
        "components": locked_components,
        "graph": {
            "order": order,
            "edges": sorted(edges, key=lambda edge: (edge["from"], edge["to"])),
        },
        "assurance": {
            "integrity": "VERIFIED",
            "compatibility": "DECLARED",
            "vulnerabilities": (
                "VERIFIED"
                if all((item.get("vulnerability") or {}).get("status") == "VERIFIED" for item in locked_components)
                else "UNVERIFIED"
            ),
            "runtime": "NOT_CERTIFIED",
            "signing": "UNSIGNED-honest",
        },
    }
    lock_digest = digest_json(lock_body)
    receipt_without_hash = {
        "schema": RECEIPT_SCHEMA,
        "id": f"factory-{lock_digest[:24]}",
        "action": "resolve-distribution",
        "decision": policy_decision,
        "honesty": "LIVE",
        "assurance": profile["assurance"],
        "runtime_certified": False,
        "signer": "UNSIGNED-honest",
        "subject": {"name": str(profile["id"]), "digest": {"sha256": lock_digest}},
        "prev_hash": GENESIS,
        "created": _timestamp(epoch),
        "note": "Metadata integrity verified. Runtime behavior and current vulnerability status require independent evidence.",
    }
    receipt = {**receipt_without_hash, "hash": digest_json(receipt_without_hash)}
    return {**lock_body, "lock_digest": f"sha256:{lock_digest}", "receipt": receipt}
