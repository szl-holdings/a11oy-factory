"""Explicit, digest-verifying artifact materialization."""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .distribution_common import (
    FactoryError,
    _artifact_filename,
    _digest_prefixed,
    _hash_file,
    _source_digest,
    _validate_lock_shape,
)


def _response_url(response: Any, fallback: str) -> str:
    """Return the post-redirect URL when the HTTP response exposes one."""

    getter = getattr(response, "geturl", None)
    if callable(getter):
        value = getter()
        if isinstance(value, str) and value.strip():
            return value
    return fallback


def _assert_allowed_url(
    uri: str,
    *,
    allowed_hosts: set[str],
    component_id: str,
    phase: str,
) -> str:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "https":
        raise FactoryError(
            f"materialize_{phase}_scheme",
            f"Refusing non-HTTPS {phase} source for {component_id}.",
            details={"component": component_id, "uri": uri},
        )
    host = (parsed.hostname or "").lower()
    if not host:
        raise FactoryError(
            f"materialize_{phase}_host",
            f"The {phase} source for {component_id!r} has no host.",
            details={"component": component_id, "uri": uri},
        )
    if allowed_hosts and host not in allowed_hosts:
        raise FactoryError(
            f"materialize_{phase}_host",
            f"Source host {host!r} is not allowed.",
            details={"component": component_id, "uri": uri, "phase": phase},
        )
    return host


def materialize_artifacts(
    lock: Mapping[str, Any],
    destination: str | os.PathLike[str],
    *,
    component_ids: Iterable[str] | None = None,
    timeout_s: float = 60.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    """Download pinned artifacts atomically and verify exact size and SHA-256.

    This function does not execute artifacts. Network access is explicit and
    restricted to policy-approved hosts. The final post-redirect URL is checked
    again so an approved origin cannot redirect materialization to an
    unapproved host or downgrade the connection.
    """

    _validate_lock_shape(lock)
    policy = lock["policy"]["effective"]
    allowed_hosts = {
        str(host).strip().lower()
        for host in (policy.get("allowed_source_hosts") or [])
        if str(host).strip()
    }
    max_bytes = int(policy.get("max_artifact_bytes", 0) or 0)
    selected = set(component_ids or [])
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    receipts: list[dict[str, Any]] = []

    for component in lock["components"]:
        component_id = str(component["id"])
        if selected and component_id not in selected:
            continue
        source = component["source"]
        if source.get("type") not in {"artifact", "oci"}:
            continue
        uri = str(source["uri"])
        origin_host = _assert_allowed_url(
            uri,
            allowed_hosts=allowed_hosts,
            component_id=component_id,
            phase="origin",
        )
        expected_size = int(source["size"])
        if max_bytes and expected_size > max_bytes:
            raise FactoryError("materialize_size", f"Artifact {component_id!r} exceeds the configured size cap.")
        expected_digest = _source_digest(source)
        if expected_digest is None:
            raise FactoryError("materialize_digest", f"Artifact {component_id!r} lacks a valid sha256 digest.")

        target = destination_path / _artifact_filename(component)
        if target.exists():
            actual_size, actual_digest = _hash_file(target)
            if actual_size == expected_size and actual_digest == expected_digest:
                receipts.append(
                    {
                        "component": component_id,
                        "path": str(target),
                        "size": actual_size,
                        "sha256": actual_digest,
                        "origin_host": origin_host,
                        "final_host": origin_host,
                        "status": "REUSED_VERIFIED",
                    }
                )
                continue

        request = urllib.request.Request(
            uri,
            headers={
                "User-Agent": "a11oy-factory/1",
                "Accept": "application/octet-stream",
            },
        )
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".partial", dir=destination_path)
        os.close(fd)
        temp_path = Path(temp_name)
        hasher = hashlib.sha256()
        count = 0
        try:
            with opener(request, timeout=timeout_s) as response, temp_path.open("wb") as output:
                final_uri = _response_url(response, uri)
                final_host = _assert_allowed_url(
                    final_uri,
                    allowed_hosts=allowed_hosts,
                    component_id=component_id,
                    phase="redirect",
                )
                content_length = response.headers.get("Content-Length") if hasattr(response, "headers") else None
                if content_length is not None:
                    declared = int(content_length)
                    if declared != expected_size:
                        raise FactoryError(
                            "materialize_declared_size",
                            f"Declared size for {component_id!r} does not match the lock.",
                            details={"expected": expected_size, "declared": declared},
                        )
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > expected_size or (max_bytes and count > max_bytes):
                        raise FactoryError("materialize_overflow", f"Artifact {component_id!r} exceeded its locked size.")
                    hasher.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            actual_digest = hasher.hexdigest()
            if count != expected_size:
                raise FactoryError(
                    "materialize_size_mismatch",
                    f"Artifact {component_id!r} size mismatch.",
                    details={"expected": expected_size, "actual": count},
                )
            if actual_digest != expected_digest:
                raise FactoryError(
                    "materialize_digest_mismatch",
                    f"Artifact {component_id!r} digest mismatch.",
                    details={"expected": expected_digest, "actual": actual_digest},
                )
            os.replace(temp_path, target)
            receipts.append(
                {
                    "component": component_id,
                    "path": str(target),
                    "size": count,
                    "sha256": actual_digest,
                    "origin_host": origin_host,
                    "final_host": final_host,
                    "status": "DOWNLOADED_VERIFIED",
                }
            )
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    missing_requested = sorted(selected - {item["component"] for item in receipts})
    if missing_requested:
        raise FactoryError(
            "materialize_missing_component",
            "One or more requested artifact components were not materialized.",
            details={"components": missing_requested},
        )
    body = {
        "schema": "a11oy.factory.materialization/v1",
        "ok": True,
        "decision": "ALLOW",
        "lock_digest": lock["lock_digest"],
        "artifacts": receipts,
        "note": "Bytes, redirect policy, sizes, and digests verified. Artifacts were not executed.",
    }
    return {**body, "receipt_hash": _digest_prefixed(body)}
