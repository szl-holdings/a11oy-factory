"""A11oy Factory public API and control surface."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE if (HERE / "a11oy_factory").is_dir() else HERE.parent
sys.path.insert(0, str(APP_ROOT))

from a11oy_factory.cells import FRONTIERS, LYTE
from a11oy_factory.compiler import compile_cell
from a11oy_factory.distribution import (
    FactoryError,
    build_plan,
    catalog_summary,
    generate_provenance,
    generate_spdx,
    read_json,
    resolve_distribution,
    verify_distribution,
)
from a11oy_factory.jobs import JOBS, search_jobs
from a11oy_factory.organs import act, roadmap

HTML = HERE / "index.html"
FACTORY_ROOT = APP_ROOT / "factory"
CATALOG_PATH = FACTORY_ROOT / "catalog.json"
PROFILE_ROOT = FACTORY_ROOT / "profiles"
MAX_BODY_BYTES = 2 * 1024 * 1024

try:
    from energy import probe
except ImportError:

    def probe(*, sample_s: float = 0.0):  # type: ignore
        return {
            "channel": "LIVE",
            "honesty": "UNAVAILABLE",
            "source": None,
            "energy_j": None,
            "note": "energy.py missing on this flatten. Channel live. Never a fabricated joule.",
        }


def _cell_payload(cell: Any) -> dict[str, Any]:
    return dict(cell.__dict__)


def _catalog() -> dict[str, Any]:
    return read_json(CATALOG_PATH)


def _profile_paths() -> dict[str, Path]:
    return {
        path.stem: path
        for path in sorted(PROFILE_ROOT.glob("*.json"))
        if path.is_file()
    }


def _profile(profile_id: str) -> dict[str, Any]:
    path = _profile_paths().get(profile_id)
    if path is None:
        raise FactoryError(
            "unknown_profile",
            f"Unknown distribution profile {profile_id!r}.",
            details={"profiles": sorted(_profile_paths())},
        )
    return read_json(path)


def _profile_summaries(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for profile_id, path in _profile_paths().items():
        profile = read_json(path)
        lock = resolve_distribution(catalog, profile)
        output.append(
            {
                "id": profile_id,
                "channel": profile["channel"],
                "assurance": profile["assurance"],
                "target": profile["target"],
                "target_spec": catalog["targets"][profile["target"]],
                "roots": profile["roots"],
                "decision": lock["policy"]["decision"],
                "warnings": lock["policy"]["warnings"],
                "lock_digest": lock["lock_digest"],
                "runtime_certified": False,
            }
        )
    return output


def _distribution_bundle(profile_id: str) -> dict[str, Any]:
    catalog = _catalog()
    profile = _profile(profile_id)
    lock = resolve_distribution(catalog, profile)
    sbom = generate_spdx(lock)
    provenance = generate_provenance(lock)
    return {
        "ok": True,
        "decision": "ALLOW",
        "profile": profile_id,
        "lock": lock,
        "plan": build_plan(lock),
        "sbom": sbom,
        "provenance": provenance,
        "verification": verify_distribution(
            catalog,
            profile,
            lock,
            sbom=sbom,
            provenance=provenance,
        ),
    }


HTML_PATHS = {"/", "/index.html"}
STATIC_JSON_PATHS = {
    "/health",
    "/healthz",
    "/readyz",
    "/api/cells",
    "/api/jobs",
    "/api/search",
    "/api/energy",
    "/api/roadmap",
    "/api/distribution",
    "/api/distribution/catalog",
    "/api/distribution/profiles",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "A11oyFactory/0.6"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, value: Any) -> None:
        self._send(
            code,
            (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _error(self, exc: FactoryError, *, code: int = 422) -> None:
        self._json(code, exc.as_dict())

    def _read_json_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as exc:
            raise FactoryError("invalid_content_length", "Content-Length must be an integer.") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise FactoryError(
                "body_too_large",
                f"Request body must not exceed {MAX_BODY_BYTES} bytes.",
            )
        raw = self.rfile.read(length) if length else b"{}"
        try:
            value = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FactoryError("invalid_json", "Request body must be a UTF-8 JSON object.") from exc
        if not isinstance(value, dict):
            raise FactoryError("invalid_body", "Request body must be a JSON object.")
        return value

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        dynamic = path.startswith("/api/roadmap/") or path.startswith("/api/distribution/profiles/")
        ok = path in HTML_PATHS or path in STATIC_JSON_PATHS or dynamic
        self.send_response(200 if ok else 404)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8" if path in HTML_PATHS else "application/json; charset=utf-8",
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        try:
            if path in HTML_PATHS:
                self._send(200, HTML.read_bytes(), "text/html; charset=utf-8")
                return
            if path in ("/health", "/healthz", "/readyz"):
                catalog = _catalog()
                profiles = _profile_summaries(catalog)
                self._json(
                    200,
                    {
                        "ok": True,
                        "service": "a11oy-factory",
                        "version": "0.6.0",
                        "bind": "BIND_AS_A11OY_PACKAGE",
                        "factory_core": {
                            "state": "LIVE",
                            "catalog": catalog_summary(catalog),
                            "profiles": len(profiles),
                            "runtime_certified": False,
                        },
                        "decision_cells": {
                            "admitted": ["lyte"],
                            "roadmap": "STARTED",
                            "frontiers": [
                                {
                                    "id": cell.id,
                                    "title": cell.title,
                                    "job": cell.job,
                                    "honesty": cell.honesty,
                                }
                                for cell in FRONTIERS
                            ],
                        },
                        "lambda_status": "Conjecture 1",
                        "energy": probe(),
                        "proven_trust": False,
                    },
                )
                return
            if path == "/api/energy":
                self._json(200, probe())
                return
            if path == "/api/cells":
                self._json(200, [_cell_payload(LYTE)] + [_cell_payload(cell) for cell in FRONTIERS])
                return
            if path == "/api/jobs":
                self._json(200, [job.__dict__ for job in JOBS])
                return
            if path == "/api/search":
                self._json(200, search_jobs((query.get("q") or [""])[0]))
                return
            if path == "/api/roadmap":
                self._json(200, roadmap())
                return
            if path.startswith("/api/roadmap/"):
                self._json(200, act(unquote(path.rsplit("/", 1)[-1]), {}))
                return
            if path == "/api/distribution":
                catalog = _catalog()
                self._json(
                    200,
                    {
                        "ok": True,
                        "state": "LIVE",
                        "summary": catalog_summary(catalog),
                        "profiles": _profile_summaries(catalog),
                        "runtime_certified": False,
                        "signing": "UNSIGNED-honest",
                    },
                )
                return
            if path == "/api/distribution/catalog":
                self._json(200, _catalog())
                return
            if path == "/api/distribution/profiles":
                catalog = _catalog()
                self._json(200, _profile_summaries(catalog))
                return
            if path.startswith("/api/distribution/profiles/"):
                profile_id = unquote(path.rsplit("/", 1)[-1])
                self._json(200, _distribution_bundle(profile_id))
                return
            self._send(404, b"not found\n", "text/plain; charset=utf-8")
        except FactoryError as exc:
            self._error(exc)
        except Exception:
            self._json(
                500,
                {
                    "ok": False,
                    "decision": "BLOCKED",
                    "error": {
                        "code": "internal_error",
                        "message": "Factory request failed closed.",
                    },
                },
            )

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            data = self._read_json_body()
            if path == "/api/compile":
                rec = compile_cell(
                    str(data.get("cell") or ""),
                    signal=str(data.get("signal") or ""),
                )
                self._json(200, rec.as_dict())
                return
            if path == "/api/search":
                self._json(200, search_jobs(str(data.get("q") or data.get("query") or "")))
                return
            if path == "/api/act":
                payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
                self._json(200, act(str(data.get("cell") or ""), payload))
                return
            if path == "/api/distribution/resolve":
                profile_id = str(data.get("profile") or "vllm-cpu-amd64")
                self._json(200, _distribution_bundle(profile_id))
                return
            if path == "/api/distribution/verify":
                profile_id = str(data.get("profile") or "")
                catalog = _catalog()
                profile = _profile(profile_id)
                lock = data.get("lock")
                if not isinstance(lock, dict):
                    raise FactoryError("missing_lock", "A lock object is required.")
                sbom = data.get("sbom") if isinstance(data.get("sbom"), dict) else None
                provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else None
                report = verify_distribution(
                    catalog,
                    profile,
                    lock,
                    sbom=sbom,
                    provenance=provenance,
                )
                self._json(200 if report["ok"] else 422, report)
                return
            self._send(404, b"not found\n", "text/plain; charset=utf-8")
        except FactoryError as exc:
            self._error(exc)
        except Exception:
            self._json(
                500,
                {
                    "ok": False,
                    "decision": "BLOCKED",
                    "error": {
                        "code": "internal_error",
                        "message": "Factory request failed closed.",
                    },
                },
            )


def main() -> None:
    port = int(os.environ.get("PORT", "7860"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(
        f"a11oy-factory listening 0.0.0.0:{port} factory=LIVE runtime_certified=false admitted={LYTE.id}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
