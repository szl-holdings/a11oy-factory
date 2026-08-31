#!/usr/bin/env python3
"""Inventory an isolated Python runtime and query OSV for exact versions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from a11oy_factory.assurance import (
    ASSURANCE_SCAN_SCHEMA,
    OSV_BATCH_ENDPOINT,
    canonical_name,
    digest_json,
    license_status,
    vulnerability_severity,
)

_LICENSE_FILE_RE = re.compile(
    r"(^|/)(licen[cs]e|copying|notice|authors?)([._-].*)?$",
    re.IGNORECASE,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pip_report_index(path: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    if path is None:
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], dict[str, Any]] = {}
    installs = report.get("install") if isinstance(report, Mapping) else None
    if not isinstance(installs, list):
        raise ValueError("pip report does not contain an install array")
    for item in installs:
        if not isinstance(item, Mapping):
            continue
        metadata = item.get("metadata")
        if not isinstance(metadata, Mapping):
            continue
        name = canonical_name(str(metadata.get("name") or ""))
        version = str(metadata.get("version") or "")
        if not name or not version:
            continue
        download = item.get("download_info") if isinstance(item.get("download_info"), Mapping) else {}
        archive = download.get("archive_info") if isinstance(download.get("archive_info"), Mapping) else {}
        hashes = archive.get("hashes") if isinstance(archive.get("hashes"), Mapping) else {}
        sha256 = hashes.get("sha256")
        if not sha256:
            legacy = str(archive.get("hash") or "")
            if legacy.startswith("sha256="):
                sha256 = legacy.partition("=")[2]
        result[(name, version)] = {
            "requested": item.get("requested") is True,
            "download_url": download.get("url"),
            "download_hashes": {"sha256": str(sha256)} if sha256 else {},
        }
    return result


def _license_files(distribution: importlib.metadata.Distribution) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for entry in distribution.files or []:
        normalized = str(entry).replace("\\", "/")
        if not _LICENSE_FILE_RE.search(normalized):
            continue
        try:
            path = Path(distribution.locate_file(entry)).resolve()
            if not path.is_file():
                continue
            evidence.append(
                {
                    "path": normalized,
                    "size": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
            )
        except (OSError, ValueError):
            continue
    evidence.sort(key=lambda item: item["path"])
    return evidence


def _inventory(
    report_index: Mapping[tuple[str, str], Mapping[str, Any]],
    excluded: set[str],
) -> list[dict[str, Any]]:
    packages: dict[str, dict[str, Any]] = {}
    for distribution in importlib.metadata.distributions():
        raw_name = str(distribution.metadata.get("Name") or "").strip()
        version = str(distribution.version or "").strip()
        name = canonical_name(raw_name)
        if not name or not version or name in excluded:
            continue
        classifiers = [
            value.partition("License ::")[2].strip()
            for value in (distribution.metadata.get_all("Classifier") or [])
            if value.startswith("License ::")
        ]
        download = report_index.get((name, version))
        if download is None and "+" in version:
            download = report_index.get((name, version.split("+", 1)[0]))
        package: dict[str, Any] = {
            "name": name,
            "display_name": raw_name,
            "version": version,
            "osv_version": version.split("+", 1)[0],
            "license_expression": distribution.metadata.get("License-Expression"),
            "license": distribution.metadata.get("License"),
            "license_classifiers": sorted(set(classifiers)),
            "license_files": _license_files(distribution),
            "requested": bool(download and download.get("requested") is True),
            "download_url": download.get("download_url") if download else None,
            "download_hashes": dict(download.get("download_hashes") or {}) if download else {},
        }
        package["license_status"] = license_status(package)
        existing = packages.get(name)
        if existing is not None and existing["version"] != version:
            raise RuntimeError(
                f"multiple installed versions observed for {name}: {existing['version']} and {version}"
            )
        packages[name] = package
    return [packages[name] for name in sorted(packages)]


def _post_json(url: str, payload: Mapping[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "a11oy-factory-assurance/0.7.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"OSV returned HTTP {response.status}")
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError("OSV response was not a JSON object")
    return value


def _query_osv(
    packages: list[dict[str, Any]],
    *,
    endpoint: str,
    timeout: float,
    retries: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    queries = [
        {
            "package": {"ecosystem": "PyPI", "name": package["name"]},
            "version": package["osv_version"],
        }
        for package in packages
    ]
    last_error: str | None = None
    response: dict[str, Any] | None = None
    attempts = 0
    for attempt in range(1, retries + 1):
        attempts = attempt
        try:
            response = _post_json(endpoint, {"queries": queries}, timeout)
            break
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(min(2 ** attempt, 12))
    if response is None:
        raise RuntimeError(f"OSV query failed after {attempts} attempts: {last_error}")

    results = response.get("results")
    if not isinstance(results, list) or len(results) != len(packages):
        raise RuntimeError(
            f"OSV result cardinality mismatch: results={len(results) if isinstance(results, list) else None} queries={len(packages)}"
        )

    vulnerabilities: list[dict[str, Any]] = []
    withdrawn = 0
    seen: set[tuple[str, str, str]] = set()
    for package, result in zip(packages, results, strict=True):
        rows = result.get("vulns") if isinstance(result, Mapping) else None
        if not isinstance(rows, list):
            continue
        for vulnerability in rows:
            if not isinstance(vulnerability, Mapping):
                continue
            if vulnerability.get("withdrawn"):
                withdrawn += 1
                continue
            vulnerability_id = str(vulnerability.get("id") or "UNKNOWN")
            key = (package["name"], package["version"], vulnerability_id)
            if key in seen:
                continue
            seen.add(key)
            severity = vulnerability_severity(vulnerability)
            references = vulnerability.get("references")
            reference_urls = []
            if isinstance(references, list):
                reference_urls = sorted(
                    {
                        str(reference.get("url"))
                        for reference in references
                        if isinstance(reference, Mapping) and reference.get("url")
                    }
                )[:12]
            vulnerabilities.append(
                {
                    "id": vulnerability_id,
                    "aliases": sorted(
                        str(alias) for alias in vulnerability.get("aliases", []) if alias
                    ),
                    "package": package["name"],
                    "version": package["version"],
                    "summary": vulnerability.get("summary"),
                    "published": vulnerability.get("published"),
                    "modified": vulnerability.get("modified"),
                    "severity": severity["label"],
                    "severity_score": severity["score"],
                    "severity_source": severity["source"],
                    "references": reference_urls,
                }
            )
    vulnerabilities.sort(key=lambda item: (item["package"], item["id"]))
    meta = {
        "endpoint": endpoint,
        "ecosystem": "PyPI",
        "complete": True,
        "query_count": len(queries),
        "result_count": len(results),
        "attempts": attempts,
        "withdrawn_matches_ignored": withdrawn,
        "last_error": last_error,
    }
    return vulnerabilities, meta


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pip-report", type=Path)
    parser.add_argument("--endpoint", default=OSV_BATCH_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--exclude", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not str(args.endpoint).startswith("https://"):
        raise SystemExit("OSV endpoint must use HTTPS")
    excluded = {canonical_name(name) for name in args.exclude}
    report_index = _pip_report_index(args.pip_report)
    packages = _inventory(report_index, excluded)
    if not packages:
        raise SystemExit("No Python distributions were found in the isolated runtime")
    vulnerabilities, osv = _query_osv(
        packages,
        endpoint=args.endpoint,
        timeout=args.timeout,
        retries=max(1, args.retries),
    )
    severity_counts: dict[str, int] = {}
    for vulnerability in vulnerabilities:
        label = str(vulnerability["severity"])
        severity_counts[label] = severity_counts.get(label, 0) + 1
    license_counts: dict[str, int] = {}
    for package in packages:
        label = str(package["license_status"])
        license_counts[label] = license_counts.get(label, 0) + 1

    body: dict[str, Any] = {
        "schema": ASSURANCE_SCAN_SCHEMA,
        "ok": True,
        "decision": "OBSERVED",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "hostname_sha256": hashlib.sha256(socket.gethostname().encode()).hexdigest(),
            "executable": sys.executable,
        },
        "pip_report_sha256": _sha256_file(args.pip_report) if args.pip_report else None,
        "packages": packages,
        "osv": osv,
        "vulnerabilities": vulnerabilities,
        "counts": {
            "packages": len(packages),
            "vulnerabilities": len(vulnerabilities),
            "severities": dict(sorted(severity_counts.items())),
            "licenses": dict(sorted(license_counts.items())),
            "packages_with_download_sha256": sum(
                1 for package in packages if package["download_hashes"].get("sha256")
            ),
        },
        "honesty": {
            "query_timestamp_scoped": True,
            "absence_of_osv_matches_is_not_absence_of_all_vulnerability": True,
            "metadata_license_is_not_legal_opinion": True,
            "runtime_certified": False,
            "signer": "UNSIGNED-honest",
        },
    }
    body["proof_sha256"] = digest_json(body)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "counts": body["counts"], "proof_sha256": body["proof_sha256"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
