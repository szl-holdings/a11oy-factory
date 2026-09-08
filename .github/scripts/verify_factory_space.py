#!/usr/bin/env python3
"""Wait for the deployed A11oy Factory Space and prove its public API is live."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi

REPO_ID = "SZLHOLDINGS/a11oy-factory"
SPACE_ORIGIN = "https://szlholdings-a11oy-factory.hf.space"
GITHUB_REPOSITORY = "szl-holdings/a11oy-factory"
SOURCE_PROVENANCE_SCHEMA = "a11oy.factory.source-provenance/v1"
SOURCE_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PROVIDER_SHA_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
EXPECTED_VERSION = "0.6.0"
EXPECTED_PROFILE_IDS = {
    "vllm-cpu-amd64",
    "vllm-cpu-arm64",
    "vllm-cuda129-amd64",
    "vllm-cuda129-arm64",
    "vllm-xpu-amd64",
}
TERMINAL_FAILURE_STAGES = {
    "BUILD_ERROR",
    "CONFIG_ERROR",
    "NO_APP_FILE",
    "RUNTIME_ERROR",
    "DELETING",
    "PAUSED",
    "STOPPED",
}
ENDPOINT_STAGES = {"RUNNING", "SLEEPING"}


class TerminalSpaceError(RuntimeError):
    """The Hub reports a settled state in which this deployment cannot serve."""


def _scalar(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _as_url(info: Any) -> str:
    host = str(getattr(info, "host", "") or "").strip()
    subdomain = str(getattr(info, "subdomain", "") or "").strip()
    if not host and subdomain:
        host = subdomain if subdomain.endswith(".hf.space") else f"{subdomain}.hf.space"
    if not host:
        raise RuntimeError("Hugging Face did not return a Space host or subdomain.")
    if not host.startswith(("https://", "http://")):
        host = f"https://{host}"
    return host.rstrip("/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Space verification endpoint redirected; request blocked.")


def _get_json(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    if base_url.rstrip("/") != SPACE_ORIGIN:
        raise TerminalSpaceError("Space origin is not the configured deployment target.")
    if path not in {"/healthz", "/api/distribution"}:
        raise TerminalSpaceError("Unexpected verification endpoint.")
    separator = "&" if "?" in path else "?"
    url = f"{base_url}{path}{separator}proof={time.time_ns()}"
    headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "User-Agent": "a11oy-factory-deployment-verifier/0.6.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        headers=headers,
    )
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200:
            raise RuntimeError(f"{path} returned HTTP {response.status}.")
        if "json" not in content_type.lower():
            raise RuntimeError(f"{path} returned unexpected content type {content_type!r}.")
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not return a JSON object.")
    return value


def _assert_contract(
    health: dict[str, Any],
    distribution: dict[str, Any],
    *,
    expected_source_sha: str | None = None,
) -> None:
    factory_core = health.get("factory_core")
    if not isinstance(factory_core, dict):
        raise RuntimeError("/healthz is missing factory_core.")
    if health.get("ok") is not True:
        raise RuntimeError("/healthz did not report ok=true.")
    if health.get("version") != EXPECTED_VERSION:
        raise RuntimeError(
            f"/healthz version is {health.get('version')!r}; waiting for {EXPECTED_VERSION!r}."
        )
    if factory_core.get("state") != "LIVE":
        raise RuntimeError("/healthz did not report factory_core.state=LIVE.")
    if factory_core.get("runtime_certified") is not False:
        raise RuntimeError("/healthz must preserve runtime_certified=false.")
    if expected_source_sha is not None:
        provenance = health.get("source_provenance")
        if not isinstance(provenance, dict):
            raise RuntimeError("/healthz is missing source_provenance.")
        if provenance.get("schema") != SOURCE_PROVENANCE_SCHEMA:
            raise RuntimeError("/healthz source provenance schema is invalid.")
        if provenance.get("state") != "BOUND":
            raise RuntimeError("/healthz source provenance is not BOUND.")
        if provenance.get("github_repository") != GITHUB_REPOSITORY:
            raise RuntimeError("/healthz source repository is not canonical.")
        if provenance.get("github_source_sha") != expected_source_sha:
            raise RuntimeError("/healthz source SHA does not match the authorized Git source.")

    if distribution.get("ok") is not True or distribution.get("state") != "LIVE":
        raise RuntimeError("/api/distribution did not report a LIVE factory.")
    if distribution.get("runtime_certified") is not False:
        raise RuntimeError("/api/distribution must preserve runtime_certified=false.")
    profiles = distribution.get("profiles")
    if not isinstance(profiles, list):
        raise RuntimeError("/api/distribution is missing profiles.")
    observed_profiles = {
        str(profile.get("id"))
        for profile in profiles
        if isinstance(profile, dict) and profile.get("id")
    }
    if observed_profiles != EXPECTED_PROFILE_IDS:
        raise RuntimeError(
            "Unexpected profile set: "
            f"observed={sorted(observed_profiles)!r} expected={sorted(EXPECTED_PROFILE_IDS)!r}."
        )
    if any(profile.get("decision") != "ALLOW" for profile in profiles if isinstance(profile, dict)):
        raise RuntimeError("At least one public profile did not resolve to ALLOW.")


def _runtime_payload(runtime: Any) -> dict[str, Any]:
    return {
        "stage": _scalar(getattr(runtime, "stage", "UNKNOWN")) or "UNKNOWN",
        "hardware": _scalar(getattr(runtime, "hardware", None)),
        "requested_hardware": _scalar(getattr(runtime, "requested_hardware", None)),
        "sleep_time": getattr(runtime, "sleep_time", None),
    }


def _current_main_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", "refs/heads/main"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("could not read current origin/main") from exc
    fields = result.stdout.strip().split()
    if result.returncode != 0 or len(fields) != 2 or fields[1] != "refs/heads/main":
        raise RuntimeError("could not prove current origin/main")
    return fields[0]


def _assert_provider_revision(info: Any, expected_revision: str) -> None:
    if not PROVIDER_SHA_PATTERN.fullmatch(expected_revision):
        raise TerminalSpaceError("Expected provider revision is missing or invalid.")
    if _scalar(getattr(info, "sha", None)) != expected_revision:
        raise TerminalSpaceError("Space revision does not match this publication.")


def _write_evidence(payload: dict[str, Any]) -> Path:
    output = Path(os.environ.get("HF_VERIFY_OUTPUT", "dist/hf-deployment-verification.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            if payload.get("ok") is False:
                handle.write("## A11oy Factory deployment blocked\n\n")
                handle.write(f"- Space: `{payload['repo_id']}`\n")
                handle.write(f"- Decision: `{payload['decision']}`\n")
                handle.write(f"- Reason: `{payload['error']}`\n")
            else:
                handle.write("## A11oy Factory deployment proof\n\n")
                handle.write(f"- Space: `{payload['repo_id']}`\n")
                handle.write(f"- Stage: `{payload['runtime']['stage']}`\n")
                handle.write(f"- Version: `{payload['health']['version']}`\n")
                handle.write(f"- Profiles: `{len(payload['distribution']['profile_ids'])}`\n")
                handle.write(f"- Runtime certified: `{payload['health']['runtime_certified']}`\n")
                handle.write(f"- Public host: `{payload['host']}`\n")
    return output


def _sanitize_text(value: Any) -> str:
    text = str(value)
    text = re.sub(
        r"(?i)(authorization:\s*bearer\s+)[^\s]+",
        r"\1[REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)([?&](?:access_token|auth|key|secret|token)=)[^&\s]+",
        r"\1[REDACTED]",
        text,
    )
    return text[:1000]


def _sanitize_observation(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            _sanitize_text(key): _sanitize_observation(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_observation(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_observation(item) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _sanitize_text(value)


def _failure_payload(
    error: str,
    observation: dict[str, Any],
    expected_source_sha: str = "",
) -> dict[str, Any]:
    return {
        "schema": "a11oy.factory.deployment-verification/v1",
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": False,
        "decision": "BLOCKED",
        "repo_id": REPO_ID,
        "github_source_sha": expected_source_sha or None,
        "error": _sanitize_text(error),
        "last_observation": _sanitize_observation(observation),
    }


def _record_failure(
    error: str,
    observation: dict[str, Any],
    expected_source_sha: str = "",
) -> int:
    payload = _failure_payload(error, observation, expected_source_sha)
    output = _write_evidence(payload)
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    print(f"blocked deployment receipt written to {output}", file=sys.stderr)
    return 1


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_ORG_TOKEN")
    if not token:
        return _record_failure(
            "HF_TOKEN/HF_ORG_TOKEN absent. Runtime verification blocked.",
            {},
        )
    expected_source_sha = os.environ.get("FACTORY_SOURCE_SHA", "").strip()
    if not SOURCE_SHA_PATTERN.fullmatch(expected_source_sha):
        return _record_failure(
            "FACTORY_SOURCE_SHA is not an exact lowercase Git SHA.",
            {},
        )

    expected_provider_sha = os.environ.get("FACTORY_PROVIDER_SHA", "").strip()
    if not PROVIDER_SHA_PATTERN.fullmatch(expected_provider_sha):
        return _record_failure(
            "FACTORY_PROVIDER_SHA is missing or invalid.",
            {},
            expected_source_sha,
        )

    timeout_seconds = int(os.environ.get("HF_VERIFY_TIMEOUT", "900"))
    poll_seconds = max(2, int(os.environ.get("HF_VERIFY_POLL", "8")))
    initial_delay = max(0, int(os.environ.get("HF_VERIFY_INITIAL_DELAY", "12")))
    deadline = time.monotonic() + timeout_seconds
    api = HfApi(token=token)
    last_observation: dict[str, Any] = {}

    if initial_delay:
        print(f"allowing {initial_delay}s for the new Space build to enter its deployment stage", flush=True)
        time.sleep(initial_delay)

    while time.monotonic() < deadline:
        try:
            runtime = api.get_space_runtime(REPO_ID)
            info = api.space_info(REPO_ID)
            _assert_provider_revision(info, expected_provider_sha)
            runtime_data = _runtime_payload(runtime)
            host = _as_url(info)
            last_observation = {
                "runtime": runtime_data,
                "host": host,
                "space_sha": _scalar(getattr(info, "sha", None)),
            }
            stage = runtime_data["stage"]
            print(
                f"space={REPO_ID} stage={stage} hardware={runtime_data['hardware']} host={host}",
                flush=True,
            )
            if stage in TERMINAL_FAILURE_STAGES:
                raise TerminalSpaceError(f"Space reached terminal failure stage {stage}.")
            if stage in ENDPOINT_STAGES:
                try:
                    health = _get_json(host, "/healthz", token=token)
                    distribution = _get_json(host, "/api/distribution", token=token)
                    _assert_contract(
                        health,
                        distribution,
                        expected_source_sha=expected_source_sha,
                    )
                    current_main_sha = _current_main_sha()
                    if current_main_sha != expected_source_sha:
                        return _record_failure(
                            "Authorized source is no longer current origin/main.",
                            {
                                **last_observation,
                                "expected_source_sha": expected_source_sha,
                                "current_main_sha": current_main_sha,
                            },
                            expected_source_sha,
                        )
                    # Recheck after endpoint probes so a concurrent Hub write
                    # during verification cannot be included in this receipt.
                    info = api.space_info(REPO_ID)
                    _assert_provider_revision(info, expected_provider_sha)
                    profiles = distribution["profiles"]
                    evidence = {
                        "schema": "a11oy.factory.deployment-verification/v1",
                        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "repo_id": REPO_ID,
                        "host": host,
                        "space_sha": _scalar(getattr(info, "sha", None)),
                        "expected_space_sha": expected_provider_sha,
                        "github_source_sha": expected_source_sha,
                        "source_provenance": health["source_provenance"],
                        "runtime": runtime_data,
                        "health": {
                            "ok": health["ok"],
                            "service": health.get("service"),
                            "version": health["version"],
                            "factory_state": health["factory_core"]["state"],
                            "runtime_certified": health["factory_core"]["runtime_certified"],
                        },
                        "distribution": {
                            "ok": distribution["ok"],
                            "state": distribution["state"],
                            "profile_ids": sorted(profile["id"] for profile in profiles),
                            "decisions": {
                                profile["id"]: profile["decision"] for profile in profiles
                            },
                            "runtime_certified": distribution["runtime_certified"],
                            "signing": distribution.get("signing"),
                        },
                    }
                    output = _write_evidence(evidence)
                    print(json.dumps(evidence, indent=2, sort_keys=True), flush=True)
                    print(f"deployment proof written to {output}", flush=True)
                    return 0
                except TerminalSpaceError:
                    raise
                except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
                    last_observation["endpoint_error"] = _sanitize_text(exc)
                    print(
                        f"runtime endpoint not ready: {_sanitize_text(exc)}",
                        flush=True,
                    )
        except TerminalSpaceError as exc:
            last_observation["terminal_error"] = str(exc)
            return _record_failure(str(exc), last_observation, expected_source_sha)
        except Exception as exc:  # Hub may transiently return 5xx during deployment.
            last_observation["hub_error"] = _sanitize_text(
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Hub runtime observation failed transiently: "
                f"{_sanitize_text(exc)}",
                flush=True,
            )
        time.sleep(poll_seconds)

    return _record_failure(
        "Timed out waiting for the deployed Space contract.",
        last_observation,
        expected_source_sha,
    )


if __name__ == "__main__":
    raise SystemExit(main())
