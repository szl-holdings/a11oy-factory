"""Shared schemas, validation, hashing, and file helpers for the AI factory."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

CATALOG_SCHEMA = "a11oy.factory.catalog/v1"
PROFILE_SCHEMA = "a11oy.factory.profile/v1"
LOCK_SCHEMA = "a11oy.factory.lock/v1"
PLAN_SCHEMA = "a11oy.factory.plan/v1"
RECEIPT_SCHEMA = "a11oy.receipt/v1"
VERIFY_SCHEMA = "a11oy.factory.verification/v1"
BUNDLE_BUILD_TYPE = "https://a-11-oy.com/factory/buildtypes/distribution-bundle/v1"
SLSA_PREDICATE = "https://slsa.dev/provenance/v1"
IN_TOTO_STATEMENT = "https://in-toto.io/Statement/v1"
GENESIS = "0" * 64

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")
_SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_SAFE_FILE_RE = re.compile(r"[^A-Za-z0-9._+-]+")

class FactoryError(ValueError):
    """Structured, serializable factory failure."""

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

def canonical_bytes(value: Any) -> bytes:
    """RFC-8785-like canonical JSON for the supported JSON value subset."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def _digest_prefixed(value: Any) -> str:
    return f"sha256:{digest_json(value)}"

def _timestamp(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _require(condition: bool, issues: list[dict[str, Any]], path: str, message: str) -> None:
    if not condition:
        issues.append({"path": path, "message": message})

def _is_string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )

def _source_digest(source: Mapping[str, Any]) -> str | None:
    digest = source.get("digest")
    if isinstance(digest, str):
        match = _SHA256_RE.fullmatch(digest.lower())
        if match:
            return match.group(1)
    return None

def _immutable_source(source: Mapping[str, Any]) -> bool:
    source_type = source.get("type")
    if source_type in {"artifact", "oci"}:
        return _source_digest(source) is not None
    if source_type == "git":
        revision = source.get("revision")
        return isinstance(revision, str) and _GIT_SHA_RE.fullmatch(revision.lower()) is not None
    return False

def validate_catalog(catalog: Mapping[str, Any]) -> None:
    issues: list[dict[str, Any]] = []
    _require(catalog.get("schema") == CATALOG_SCHEMA, issues, "schema", f"must equal {CATALOG_SCHEMA}")
    _require(isinstance(catalog.get("name"), str) and bool(catalog.get("name", "").strip()), issues, "name", "must be a non-empty string")
    targets = catalog.get("targets")
    _require(isinstance(targets, dict) and bool(targets), issues, "targets", "must be a non-empty object")
    if isinstance(targets, dict):
        for target_id, target in targets.items():
            base = f"targets.{target_id}"
            _require(bool(_ID_RE.fullmatch(str(target_id))), issues, base, "invalid target id")
            _require(isinstance(target, dict), issues, base, "must be an object")
            if isinstance(target, dict):
                for field in ("os", "arch", "accelerator", "python"):
                    _require(
                        isinstance(target.get(field), str) and bool(target.get(field, "").strip()),
                        issues,
                        f"{base}.{field}",
                        "must be a non-empty string",
                    )

    components = catalog.get("components")
    _require(isinstance(components, list) and bool(components), issues, "components", "must be a non-empty array")
    seen: set[str] = set()
    if isinstance(components, list):
        for index, component in enumerate(components):
            base = f"components[{index}]"
            _require(isinstance(component, dict), issues, base, "must be an object")
            if not isinstance(component, dict):
                continue
            component_id = component.get("id")
            _require(isinstance(component_id, str) and bool(_ID_RE.fullmatch(component_id)), issues, f"{base}.id", "invalid component id")
            if isinstance(component_id, str):
                _require(component_id not in seen, issues, f"{base}.id", "duplicate component id")
                seen.add(component_id)
            for field in ("version", "kind", "license", "supplier", "description"):
                _require(
                    isinstance(component.get(field), str) and bool(component.get(field, "").strip()),
                    issues,
                    f"{base}.{field}",
                    "must be a non-empty string",
                )
            component_targets = component.get("targets")
            _require(_is_string_list(component_targets, nonempty=True), issues, f"{base}.targets", "must be a non-empty string array")
            if isinstance(component_targets, list) and isinstance(targets, dict):
                for target_id in component_targets:
                    _require(target_id == "*" or target_id in targets, issues, f"{base}.targets", f"unknown target {target_id!r}")
            requires = component.get("requires", [])
            _require(_is_string_list(requires), issues, f"{base}.requires", "must be a string array")
            if isinstance(requires, list):
                _require(len(requires) == len(set(requires)), issues, f"{base}.requires", "must not contain duplicates")
                if isinstance(component_id, str):
                    _require(component_id not in requires, issues, f"{base}.requires", "component cannot require itself")
            source = component.get("source")
            _require(isinstance(source, dict), issues, f"{base}.source", "must be an object")
            if isinstance(source, dict):
                source_type = source.get("type")
                _require(source_type in {"artifact", "oci", "git"}, issues, f"{base}.source.type", "must be artifact, oci, or git")
                uri = source.get("uri")
                _require(isinstance(uri, str) and bool(uri.strip()), issues, f"{base}.source.uri", "must be a non-empty string")
                if isinstance(uri, str):
                    parsed = urllib.parse.urlparse(uri)
                    _require(parsed.scheme == "https", issues, f"{base}.source.uri", "must use https")
                    _require(bool(parsed.hostname), issues, f"{base}.source.uri", "must include a host")
                if source_type in {"artifact", "oci"}:
                    _require(_source_digest(source) is not None, issues, f"{base}.source.digest", "must be sha256:<64 lowercase hex>")
                    size = source.get("size")
                    _require(isinstance(size, int) and not isinstance(size, bool) and size >= 0, issues, f"{base}.source.size", "must be a non-negative integer")
                if source_type == "git":
                    revision = source.get("revision")
                    _require(isinstance(revision, str) and bool(revision.strip()), issues, f"{base}.source.revision", "must be a non-empty string")
            evidence = component.get("evidence", [])
            _require(isinstance(evidence, list), issues, f"{base}.evidence", "must be an array")
            if isinstance(evidence, list):
                for evidence_index, item in enumerate(evidence):
                    eb = f"{base}.evidence[{evidence_index}]"
                    _require(isinstance(item, dict), issues, eb, "must be an object")
                    if isinstance(item, dict):
                        _require(isinstance(item.get("type"), str) and bool(item.get("type", "").strip()), issues, f"{eb}.type", "must be a non-empty string")
                        _require(isinstance(item.get("uri"), str) and item.get("uri", "").startswith("https://"), issues, f"{eb}.uri", "must be an https URI")
            vulnerability = component.get("vulnerability")
            _require(isinstance(vulnerability, dict), issues, f"{base}.vulnerability", "must be an object")
            if isinstance(vulnerability, dict):
                _require(
                    vulnerability.get("status") in {"VERIFIED", "UNVERIFIED", "BLOCKED"},
                    issues,
                    f"{base}.vulnerability.status",
                    "must be VERIFIED, UNVERIFIED, or BLOCKED",
                )
            build = component.get("build", {})
            _require(isinstance(build, dict), issues, f"{base}.build", "must be an object")
            if isinstance(build, dict):
                _require(isinstance(build.get("network", False), bool), issues, f"{base}.build.network", "must be boolean")
                steps = build.get("steps", [])
                _require(isinstance(steps, list), issues, f"{base}.build.steps", "must be an array")
                if isinstance(steps, list):
                    for step_index, step in enumerate(steps):
                        sb = f"{base}.build.steps[{step_index}]"
                        _require(isinstance(step, dict), issues, sb, "must be an object")
                        if isinstance(step, dict):
                            _require(isinstance(step.get("name"), str) and bool(step.get("name", "").strip()), issues, f"{sb}.name", "must be non-empty")
                            _require(_is_string_list(step.get("argv"), nonempty=True), issues, f"{sb}.argv", "must be a non-empty argv array")

    if isinstance(components, list):
        component_ids = {item.get("id") for item in components if isinstance(item, dict)}
        for index, component in enumerate(components):
            if isinstance(component, dict) and isinstance(component.get("requires", []), list):
                for dependency in component.get("requires", []):
                    _require(dependency in component_ids, issues, f"components[{index}].requires", f"unknown component {dependency!r}")

    defaults = catalog.get("policy_defaults", {})
    _require(isinstance(defaults, dict), issues, "policy_defaults", "must be an object")
    if issues:
        raise FactoryError("invalid_catalog", "Catalog validation failed.", details={"issues": issues})

def validate_profile(profile: Mapping[str, Any], catalog: Mapping[str, Any]) -> None:
    issues: list[dict[str, Any]] = []
    _require(profile.get("schema") == PROFILE_SCHEMA, issues, "schema", f"must equal {PROFILE_SCHEMA}")
    profile_id = profile.get("id")
    _require(isinstance(profile_id, str) and bool(_ID_RE.fullmatch(profile_id)), issues, "id", "invalid profile id")
    for field in ("channel", "assurance", "target"):
        _require(isinstance(profile.get(field), str) and bool(profile.get(field, "").strip()), issues, field, "must be a non-empty string")
    roots = profile.get("roots")
    _require(_is_string_list(roots, nonempty=True), issues, "roots", "must be a non-empty string array")
    if isinstance(roots, list):
        _require(len(roots) == len(set(roots)), issues, "roots", "must not contain duplicates")
    epoch = profile.get("source_date_epoch")
    _require(isinstance(epoch, int) and not isinstance(epoch, bool) and epoch >= 0, issues, "source_date_epoch", "must be a non-negative integer")
    policy = profile.get("policy", {})
    _require(isinstance(policy, dict), issues, "policy", "must be an object")

    targets = catalog.get("targets", {})
    _require(profile.get("target") in targets, issues, "target", "unknown catalog target")
    component_ids = {item.get("id") for item in catalog.get("components", []) if isinstance(item, dict)}
    if isinstance(roots, list):
        for root in roots:
            _require(root in component_ids, issues, "roots", f"unknown root {root!r}")
    if issues:
        raise FactoryError("invalid_profile", "Profile validation failed.", details={"issues": issues})

def read_json(path: str | os.PathLike[str]) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FactoryError("file_not_found", f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FactoryError(
            "invalid_json",
            f"Invalid JSON in {path}.",
            details={"line": exc.lineno, "column": exc.colno, "message": exc.msg},
        ) from exc
    if not isinstance(value, dict):
        raise FactoryError("invalid_document", f"Top-level JSON document must be an object: {path}")
    return value

def catalog_summary(catalog: Mapping[str, Any]) -> dict[str, Any]:
    validate_catalog(catalog)
    components = catalog["components"]
    return {
        "schema": CATALOG_SCHEMA,
        "name": catalog["name"],
        "components": len(components),
        "targets": sorted(catalog["targets"]),
        "licenses": sorted({component["license"] for component in components}),
        "accelerators": sorted({target["accelerator"] for target in catalog["targets"].values()}),
        "vulnerability": {
            status: sum(1 for component in components if component["vulnerability"]["status"] == status)
            for status in ("VERIFIED", "UNVERIFIED", "BLOCKED")
        },
        "catalog_digest": _digest_prefixed(catalog),
        "runtime_certified": False,
    }

def _validate_lock_shape(lock: Mapping[str, Any]) -> None:
    if lock.get("schema") != LOCK_SCHEMA:
        raise FactoryError("invalid_lock", f"Lock schema must equal {LOCK_SCHEMA}.")
    digest = lock.get("lock_digest")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise FactoryError("invalid_lock", "Lock digest must be sha256:<64 lowercase hex>.")
    if not isinstance(lock.get("components"), list) or not isinstance(lock.get("profile"), dict):
        raise FactoryError("invalid_lock", "Lock components/profile are malformed.")

def _artifact_filename(component: Mapping[str, Any]) -> str:
    source = component["source"]
    explicit = source.get("filename")
    if isinstance(explicit, str) and explicit:
        candidate = explicit
    else:
        candidate = Path(urllib.parse.unquote(urllib.parse.urlparse(source["uri"]).path)).name
    candidate = _SAFE_FILE_RE.sub("_", candidate).strip("._")
    if not candidate:
        candidate = f"{component['id']}-{component['version']}.artifact"
    return candidate[:240]

def _spdx_safe(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9.-]+", "-", str(value)).strip("-")
    return cleaned or "unknown"

def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise

def _hash_file(path: Path) -> tuple[int, str]:
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            hasher.update(chunk)
    return size, hasher.hexdigest()
