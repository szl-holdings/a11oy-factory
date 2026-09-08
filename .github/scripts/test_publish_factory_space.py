#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("publish_factory_space.py")
SPEC = importlib.util.spec_from_file_location("publish_factory_space", MODULE_PATH)
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)

SOURCE_SHA = "a" * 40
REPOSITORY_ROOT = MODULE_PATH.parents[2]


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def initialize_repository(root: Path) -> None:
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.name", "Factory Publisher Test")
    run_git(root, "config", "user.email", "factory-publisher@example.invalid")
    (root / "tracked.txt").write_text("authorized\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    run_git(root, "commit", "--quiet", "--no-gpg-sign", "-m", "authorized source")


class FakeApi:
    def __init__(
        self,
        *,
        info=None,
        error: Exception | None = None,
        upload_error: Exception | None = None,
    ) -> None:
        self.info = info or SimpleNamespace(private=True, sdk="docker", sha="d" * 40)
        self.error = error
        self.upload_error = upload_error
        self.uploads: list[dict] = []

    def space_info(self, repo_id: str):
        if self.error:
            raise self.error
        self.repo_id = repo_id
        return self.info

    def upload_folder(self, **kwargs):
        if self.upload_error:
            raise self.upload_error
        self.uploads.append(kwargs)
        return SimpleNamespace(oid="b" * 40)


class PublisherTests(unittest.TestCase):
    def test_runtime_provenance_is_not_excluded_by_repository_gitignore(self) -> None:
        result = subprocess.run(
            [
                "git",
                "check-ignore",
                "--no-index",
                "--quiet",
                publisher.PROVENANCE_RELATIVE_PATH.as_posix(),
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode,
            1,
            "generated runtime provenance must be included in the provider upload manifest",
        )

    def test_provider_read_failure_never_enters_a_write_path(self) -> None:
        api = FakeApi(error=RuntimeError("network unavailable"))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(publisher.PublicationBlocked, "readback failed"):
                publisher.publish_existing_space(
                    api,
                    Path(directory),
                    SOURCE_SHA,
                    prove=lambda _root, _sha: None,
                )
        self.assertEqual(api.uploads, [])

    def test_space_identity_must_be_private_docker(self) -> None:
        for info in (
            SimpleNamespace(private=False, sdk="docker", sha="d" * 40),
            SimpleNamespace(private=True, sdk="gradio", sha="d" * 40),
        ):
            api = FakeApi(info=info)
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(publisher.PublicationBlocked, "private"):
                    publisher.publish_existing_space(
                        api,
                        Path(directory),
                        SOURCE_SHA,
                        prove=lambda _root, _sha: None,
                    )
            self.assertEqual(api.uploads, [])

    def test_runtime_provenance_and_binding_precede_upload(self) -> None:
        events: list[str] = []
        api = FakeApi()
        original_upload = api.upload_folder

        def upload(**kwargs):
            events.append("upload")
            return original_upload(**kwargs)

        api.upload_folder = upload
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def prove(proved_root: Path, proved_sha: str) -> None:
                self.assertEqual(proved_root, root)
                self.assertEqual(proved_sha, SOURCE_SHA)
                self.assertTrue((root / publisher.PROVENANCE_RELATIVE_PATH).is_file())
                events.append("prove")

            publisher.publish_existing_space(api, root, SOURCE_SHA, prove=prove)
            payload = json.loads((root / publisher.PROVENANCE_RELATIVE_PATH).read_text())

        self.assertEqual(events, ["prove", "upload"])
        self.assertEqual(payload["github_source_sha"], SOURCE_SHA)
        self.assertEqual(payload["github_repository"], publisher.GITHUB_REPOSITORY)
        self.assertIn(SOURCE_SHA, api.uploads[0]["commit_message"])
        self.assertEqual(api.uploads[0]["parent_commit"], "d" * 40)
        self.assertEqual(api.uploads[0]["delete_patterns"], "*")

    def test_missing_provider_revision_blocks_before_upload(self) -> None:
        api = FakeApi(info=SimpleNamespace(private=True, sdk="docker", sha=None))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(publisher.PublicationBlocked, "provider revision"):
                publisher.publish_existing_space(
                    api,
                    Path(directory),
                    SOURCE_SHA,
                    prove=lambda _root, _sha: None,
                )
        self.assertEqual(api.uploads, [])

    def test_missing_uploaded_revision_cannot_be_reported_as_success(self) -> None:
        with self.assertRaisesRegex(publisher.PublicationBlocked, "not proven"):
            publisher.provider_revision(SimpleNamespace(oid=None, commit_id=None))
        self.assertEqual(
            publisher.provider_revision(SimpleNamespace(oid="b" * 40)),
            "b" * 40,
        )

    def test_upload_error_is_recorded_as_unknown_after_attempt(self) -> None:
        api = FakeApi(upload_error=RuntimeError("sensitive provider detail"))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                publisher.ProviderMutationUnproven,
                "settled revision is unknown",
            ) as raised:
                publisher.publish_existing_space(
                    api,
                    Path(directory),
                    SOURCE_SHA,
                    prove=lambda _root, _sha: None,
                )
        self.assertNotIn("sensitive provider detail", str(raised.exception))

    def test_blocked_publication_receipt_is_secret_free_and_classified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = publisher.write_blocked_receipt(
                Path(directory),
                SOURCE_SHA,
                reason="provider write raised RuntimeError; settled revision is unknown",
                mutation_state="UNKNOWN_AFTER_ATTEMPT",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(payload["phase"], "publication")
        self.assertEqual(payload["provider_mutation"], "UNKNOWN_AFTER_ATTEMPT")
        self.assertEqual(payload["github_source_sha"], SOURCE_SHA)

    def test_provider_client_setup_failure_retains_not_attempted_receipt(self) -> None:
        fake_hub = types.ModuleType("huggingface_hub")

        class FailingApi:
            def __init__(self, *, token: str) -> None:
                raise RuntimeError("constructor detail must not escape")

        fake_hub.HfApi = FailingApi
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "deployment.json"
            environment = {
                "FACTORY_SOURCE_SHA": SOURCE_SHA,
                "GITHUB_REPOSITORY": publisher.GITHUB_REPOSITORY,
                "GITHUB_WORKSPACE": directory,
                "HF_TOKEN": "test-only-token",
                "HF_VERIFY_OUTPUT": str(output),
            }
            with (
                patch.dict(os.environ, environment, clear=False),
                patch.dict(sys.modules, {"huggingface_hub": fake_hub}),
            ):
                result = publisher.main()
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 1)
        self.assertEqual(payload["provider_mutation"], "NOT_ATTEMPTED")
        self.assertNotIn("constructor detail", json.dumps(payload))

    def test_modified_tracked_file_blocks_upload_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            publisher.write_source_provenance(root, SOURCE_SHA)
            (root / "tracked.txt").write_text("dirty\n", encoding="utf-8")

            with self.assertRaisesRegex(publisher.PublicationBlocked, "authorized Git tree"):
                publisher.prove_upload_workspace_clean(root)

    def test_staged_file_blocks_upload_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            publisher.write_source_provenance(root, SOURCE_SHA)
            (root / "staged.txt").write_text("staged\n", encoding="utf-8")
            run_git(root, "add", "staged.txt")

            with self.assertRaisesRegex(publisher.PublicationBlocked, "authorized Git tree"):
                publisher.prove_upload_workspace_clean(root)

    def test_untracked_file_blocks_upload_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            publisher.write_source_provenance(root, SOURCE_SHA)
            (root / "untracked.txt").write_text("untracked\n", encoding="utf-8")

            with self.assertRaisesRegex(publisher.PublicationBlocked, "authorized Git tree"):
                publisher.prove_upload_workspace_clean(root)

    def test_generated_provenance_is_the_only_allowed_workspace_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            provenance = publisher.write_source_provenance(root, SOURCE_SHA)

            publisher.prove_upload_workspace_clean(root)
            payload = json.loads(provenance.read_text(encoding="utf-8"))

        self.assertEqual(payload["github_source_sha"], SOURCE_SHA)

    def test_validated_provider_revision_is_written_to_github_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "github-output.txt"
            with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}, clear=False):
                publisher.write_uploaded_revision_output("b" * 40)

            self.assertEqual(output.read_text(encoding="utf-8"), f"uploaded_revision={'b' * 40}\n")

    def test_source_binding_requires_head_and_exact_current_main(self) -> None:
        def matching_git(_root: Path, *args: str) -> str:
            if args[:2] == ("rev-parse", "HEAD"):
                return SOURCE_SHA
            if args and args[0] == "status":
                return f"?? {publisher.PROVENANCE_RELATIVE_PATH.as_posix()}"
            return f"{SOURCE_SHA}\trefs/heads/main"

        publisher.prove_source_binding(Path("."), SOURCE_SHA, git=matching_git)

        def stale_git(_root: Path, *args: str) -> str:
            if args[:2] == ("rev-parse", "HEAD"):
                return SOURCE_SHA
            if args and args[0] == "status":
                return f"?? {publisher.PROVENANCE_RELATIVE_PATH.as_posix()}"
            return f"{'c' * 40}\trefs/heads/main"

        with self.assertRaisesRegex(publisher.PublicationBlocked, "current origin/main"):
            publisher.prove_source_binding(Path("."), SOURCE_SHA, git=stale_git)


if __name__ == "__main__":
    unittest.main()
