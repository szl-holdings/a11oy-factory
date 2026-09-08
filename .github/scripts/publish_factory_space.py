#!/usr/bin/env python3
"""Update the existing protected A11oy Factory Space from an exact Git source."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ID = "SZLHOLDINGS/a11oy-factory"
GITHUB_REPOSITORY = "szl-holdings/a11oy-factory"
SOURCE_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PROVIDER_SHA_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
PROVENANCE_SCHEMA = "a11oy.factory.source-provenance/v1"
PROVENANCE_RELATIVE_PATH = Path("factory/source-provenance.json")
IGNORE = [
    ".git",
    ".github",
    "node_modules",
    "artifacts",
    "screenshots",
    "attachments",
    ".grok",
    "AGENTS.md",
    "dist",
    ".output",
]


class PublicationBlocked(RuntimeError):
    """A required readback or source binding was not proven."""


class ProviderMutationUnproven(PublicationBlocked):
    """A provider write was attempted but its settled revision is unknown."""


def write_blocked_receipt(
    root: Path,
    source_sha: str,
    *,
    reason: str,
    mutation_state: str,
) -> Path:
    output = Path(
        os.environ.get("HF_VERIFY_OUTPUT", "dist/hf-deployment-verification.json")
    )
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "a11oy.factory.deployment-verification/v1",
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": False,
        "decision": "BLOCKED",
        "phase": "publication",
        "repo_id": REPO_ID,
        "github_source_sha": (
            source_sha if SOURCE_SHA_PATTERN.fullmatch(source_sha) else None
        ),
        "provider_mutation": mutation_state,
        "error": reason,
    }
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublicationBlocked(f"git {' '.join(args)} could not be executed") from exc
    if result.returncode != 0:
        raise PublicationBlocked(f"git {' '.join(args)} failed")
    return result.stdout.strip()


def prove_source_binding(
    root: Path,
    source_sha: str,
    *,
    git: Callable[..., str] = _git,
) -> None:
    if not SOURCE_SHA_PATTERN.fullmatch(source_sha):
        raise PublicationBlocked("FACTORY_SOURCE_SHA must be exact lowercase 40-character Git SHA")
    head = git(root, "rev-parse", "HEAD")
    if head != source_sha:
        raise PublicationBlocked("checked-out Git HEAD does not match FACTORY_SOURCE_SHA")
    remote_line = git(root, "ls-remote", "--heads", "origin", "refs/heads/main")
    fields = remote_line.split()
    if len(fields) != 2 or fields[1] != "refs/heads/main" or fields[0] != source_sha:
        raise PublicationBlocked("FACTORY_SOURCE_SHA is not the exact current origin/main")
    prove_upload_workspace_clean(root, git=git)


def prove_upload_workspace_clean(
    root: Path,
    *,
    git: Callable[..., str] = _git,
) -> None:
    status = git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
    )
    entries = [line for line in status.splitlines() if line]
    expected = f"?? {PROVENANCE_RELATIVE_PATH.as_posix()}"
    if entries != [expected]:
        raise PublicationBlocked(
            "upload workspace is not the authorized Git tree plus generated provenance"
        )


def write_source_provenance(root: Path, source_sha: str) -> Path:
    path = root / PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": PROVENANCE_SCHEMA,
        "github_repository": GITHUB_REPOSITORY,
        "github_source_sha": source_sha,
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def publish_existing_space(
    api: Any,
    root: Path,
    source_sha: str,
    *,
    prove: Callable[[Path, str], None] = prove_source_binding,
) -> Any:
    try:
        existing = api.space_info(REPO_ID)
    except Exception as exc:
        raise PublicationBlocked(
            f"Space readback failed with {type(exc).__name__}; provider mutation blocked"
        ) from None

    sdk = str(getattr(getattr(existing, "sdk", None), "value", getattr(existing, "sdk", "")))
    if getattr(existing, "private", None) is not True or sdk.lower() != "docker":
        raise PublicationBlocked("existing Space must be private and use the Docker SDK")
    provider_sha = str(getattr(existing, "sha", "") or "")
    if not PROVIDER_SHA_PATTERN.fullmatch(provider_sha):
        raise PublicationBlocked("existing Space did not return an immutable provider revision")

    write_source_provenance(root, source_sha)
    # This is intentionally the final operation before the provider write.
    prove(root, source_sha)
    try:
        return api.upload_folder(
            repo_id=REPO_ID,
            repo_type="space",
            folder_path=str(root),
            commit_message=f"Sync A11oy factory Space from GitHub source {source_sha}",
            ignore_patterns=IGNORE,
            delete_patterns="*",
            parent_commit=provider_sha,
        )
    except Exception as exc:
        raise ProviderMutationUnproven(
            f"provider write raised {type(exc).__name__}; settled revision is unknown"
        ) from None


def provider_revision(result: Any) -> str:
    revision = str(
        getattr(result, "oid", None)
        or getattr(result, "commit_id", None)
        or ""
    )
    if not PROVIDER_SHA_PATTERN.fullmatch(revision):
        raise ProviderMutationUnproven(
            "provider write returned no immutable revision; upload is not proven"
        )
    return revision


def write_uploaded_revision_output(revision: str) -> None:
    if not PROVIDER_SHA_PATTERN.fullmatch(revision):
        raise ProviderMutationUnproven(
            "unvalidated provider revision cannot be exported to the workflow"
        )
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    try:
        with Path(output).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"uploaded_revision={revision}\n")
    except OSError:
        raise ProviderMutationUnproven(
            "validated provider revision could not be exported to the workflow"
        ) from None


def main() -> int:
    root = Path(os.environ.get("GITHUB_WORKSPACE") or ".").resolve()
    source_sha = os.environ.get("FACTORY_SOURCE_SHA", "").strip()
    token = os.environ.get("HF_TOKEN")
    if not token:
        output = write_blocked_receipt(
            root,
            source_sha,
            reason="HF_TOKEN absent. Hub mutation blocked.",
            mutation_state="NOT_ATTEMPTED",
        )
        print(f"HF_TOKEN absent. Blocked receipt written to {output}.", file=sys.stderr)
        return 1

    repository = os.environ.get("GITHUB_REPOSITORY", GITHUB_REPOSITORY).lower()
    if repository != GITHUB_REPOSITORY:
        output = write_blocked_receipt(
            root,
            source_sha,
            reason="Unexpected GitHub repository identity. Hub mutation blocked.",
            mutation_state="NOT_ATTEMPTED",
        )
        print(f"Unexpected repository. Blocked receipt written to {output}.", file=sys.stderr)
        return 1

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        result = publish_existing_space(api, root, source_sha)
        uploaded_revision = provider_revision(result)
        write_uploaded_revision_output(uploaded_revision)
    except ProviderMutationUnproven as exc:
        output = write_blocked_receipt(
            root,
            source_sha,
            reason=str(exc),
            mutation_state="UNKNOWN_AFTER_ATTEMPT",
        )
        print(f"{exc}. Blocked receipt written to {output}.", file=sys.stderr)
        return 1
    except PublicationBlocked as exc:
        output = write_blocked_receipt(
            root,
            source_sha,
            reason=f"{exc}. Hub mutation blocked.",
            mutation_state="NOT_ATTEMPTED",
        )
        print(f"{exc}. Blocked receipt written to {output}.", file=sys.stderr)
        return 1
    except Exception as exc:
        output = write_blocked_receipt(
            root,
            source_sha,
            reason=f"Provider setup failed with {type(exc).__name__}.",
            mutation_state="NOT_ATTEMPTED",
        )
        print(
            f"Provider setup failed with {type(exc).__name__}; "
            f"blocked receipt written to {output}.",
            file=sys.stderr,
        )
        return 1
    print(f"uploaded {REPO_ID} provider_revision={uploaded_revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
