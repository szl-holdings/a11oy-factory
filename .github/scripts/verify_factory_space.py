#!/usr/bin/env python3
"""Wait for the deployed A11oy Factory Space and prove its public API is live."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi

REPO_ID = "SZLHOLDINGS/a11oy-factory"
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
    "RUNTIME_ERROR",
    "DELETING",
    "PAUSED",
    "STOPPED",
}


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


def _get_json(base_url: str, path: str, *, timeout: float = 15.0) -> dict[str, Any]:
    separator = "&" if "?" in path else "?"
    url = f"{base_url}{path}{separator}proof={time.time_ns()}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "User-Agent": "a11oy-factory-deployment-verifier/0.6.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200:
            raise RuntimeError(f"{path} returned HTTP {response.status}.")
        if "json" not in content_type.lower():
            raise RuntimeError(f"{path} returned unexpected content type {content_type!r}.")
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not return a JSON object.")
    return value


def _assert_contract(health: dict[str, Any], distribution: dict[str, Any]) -> None:
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
        "stage": str(getattr(runtime, "stage", "UNKNOWN")),
        "hardware": getattr(runtime, "hardware", None),
        "requested_hardware": getattr(runtime, "requested_hardware", None),
        "sleep_time": getattr(runtime, "sleep_time", None),
    }


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
            handle.write("## A11oy Factory deployment proof\n\n")
            handle.write(f"- Space: `{payload['repo_id']}`\n")
            handle.write(f"- Stage: `{payload['runtime']['stage']}`\n")
            handle.write(f"- Version: `{payload['health']['version']}`\n")
            handle.write(f"- Profiles: `{len(payload['distribution']['profile_ids'])}`\n")
            handle.write(f"- Runtime certified: `{payload['health']['runtime_certified']}`\n")
            handle.write(f"- Public host: `{payload['host']}`\n")
    return output


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_ORG_TOKEN")
    if not token:
        print("HF_TOKEN/HF_ORG_TOKEN absent. Runtime verification blocked.", file=sys.stderr)
        return 1

    timeout_seconds = int(os.environ.get("HF_VERIFY_TIMEOUT", "900"))
    poll_seconds = max(2, int(os.environ.get("HF_VERIFY_POLL", "8")))
    deadline = time.monotonic() + timeout_seconds
    api = HfApi(token=token)
    last_observation: dict[str, Any] = {}

    while time.monotonic() < deadline:
        try:
            runtime = api.get_space_runtime(REPO_ID)
            info = api.space_info(REPO_ID)
            runtime_data = _runtime_payload(runtime)
            host = _as_url(info)
            last_observation = {
                "runtime": runtime_data,
                "host": host,
                "space_sha": getattr(info, "sha", None),
            }
            stage = runtime_data["stage"]
            print(
                f"space={REPO_ID} stage={stage} hardware={runtime_data['hardware']} host={host}",
                flush=True,
            )
            if stage in TERMINAL_FAILURE_STAGES:
                raise RuntimeError(f"Space reached terminal failure stage {stage}.")
            if stage == "RUNNING":
                try:
                    health = _get_json(host, "/healthz")
                    distribution = _get_json(host, "/api/distribution")
                    _assert_contract(health, distribution)
                    profiles = distribution["profiles"]
                    evidence = {
                        "schema": "a11oy.factory.deployment-verification/v1",
                        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "repo_id": REPO_ID,
                        "host": host,
                        "space_sha": getattr(info, "sha", None),
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
                except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
                    last_observation["endpoint_error"] = str(exc)
                    print(f"runtime endpoint not ready: {exc}", flush=True)
        except RuntimeError:
            raise
        except Exception as exc:  # Hub may transiently return 5xx during deployment.
            last_observation["hub_error"] = f"{type(exc).__name__}: {exc}"
            print(f"Hub runtime observation failed transiently: {exc}", flush=True)
        time.sleep(poll_seconds)

    print(
        json.dumps(
            {
                "ok": False,
                "decision": "BLOCKED",
                "error": "Timed out waiting for the deployed Space contract.",
                "last_observation": last_observation,
            },
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
