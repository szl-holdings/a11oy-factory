#!/usr/bin/env python3
"""Create or update the protected A11oy factory Space. Not a seventh public Space."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "SZLHOLDINGS/a11oy-factory"
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


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_ORG_TOKEN")
    if not token:
        print("HF_TOKEN/HF_ORG_TOKEN absent. Hub mutation blocked.", file=sys.stderr)
        return 1

    root = Path(os.environ.get("GITHUB_WORKSPACE") or ".").resolve()
    api = HfApi(token=token)

    info = api.create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        private=True,
        space_sdk="docker",
        exist_ok=True,
    )
    print(f"space {REPO_ID} url={getattr(info, 'url', info)}")

    try:
        api.update_repo_visibility(repo_id=REPO_ID, repo_type="space", private=True)
    except Exception as exc:  # noqa: BLE001 — visibility is best-effort; create already requested private
        print(f"visibility update skipped: {exc}")

    api.upload_folder(
        repo_id=REPO_ID,
        repo_type="space",
        folder_path=str(root),
        commit_message="Bind protected A11oy factory Space (not a second flagship)",
        ignore_patterns=IGNORE,
    )
    print(f"uploaded {REPO_ID} as private docker space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
