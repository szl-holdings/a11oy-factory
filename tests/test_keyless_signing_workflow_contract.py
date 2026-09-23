# Copyright 2026 SZL Holdings — SPDX-License-Identifier: Apache-2.0
"""Regression tests for the assurance-to-signing artifact contract."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from a11oy_factory.assurance import AssuranceError
from a11oy_factory.distribution_resolver import resolve_distribution


ROOT = Path(__file__).resolve().parents[1]
SIGNING_WORKFLOW = ROOT / ".github" / "workflows" / "factory-keyless-signing.yml"
ASSURANCE_WORKFLOW = ROOT / ".github" / "workflows" / "factory-supply-chain-assurance.yml"
SUBJECT_BUILDER_PATH = ROOT / "scripts" / "build_assurance_signing_subject.py"
SUBJECT_BUILDER_SPEC = importlib.util.spec_from_file_location(
    "a11oy_factory_test_subject_builder",
    SUBJECT_BUILDER_PATH,
)
assert SUBJECT_BUILDER_SPEC and SUBJECT_BUILDER_SPEC.loader
SUBJECT_BUILDER = importlib.util.module_from_spec(SUBJECT_BUILDER_SPEC)
sys.modules[SUBJECT_BUILDER_SPEC.name] = SUBJECT_BUILDER
SUBJECT_BUILDER_SPEC.loader.exec_module(SUBJECT_BUILDER)


class KeylessSigningWorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signing = SIGNING_WORKFLOW.read_text(encoding="utf-8")
        self.assurance = ASSURANCE_WORKFLOW.read_text(encoding="utf-8")
        self.subject_builder = SUBJECT_BUILDER_PATH.read_text(encoding="utf-8")

    @staticmethod
    def _resolved_lock() -> dict:
        catalog = json.loads((ROOT / "factory" / "catalog.json").read_text(encoding="utf-8"))
        profile = json.loads(
            (ROOT / "factory" / "profiles" / "vllm-cpu-amd64.json").read_text(
                encoding="utf-8"
            )
        )
        return resolve_distribution(catalog, profile)

    def test_runtime_evidence_filename_matches_producer(self) -> None:
        self.assertIn(
            "dist/assurance/runtime/runtime-execution.json",
            self.assurance,
        )
        self.assertIn(
            'RUNTIME_PROOF="$(find dist/signing/source -type f -name runtime-execution.json -print -quit)"',
            self.signing,
        )
        self.assertNotIn("runtime-proof.json", self.signing)

    def test_quoted_heredoc_reads_environment_not_literal_shell_syntax(self) -> None:
        self.assertIn("import os", self.signing)
        self.assertIn(
            'Path(os.environ["INITIAL_STABLE_VERDICT"])',
            self.signing,
        )
        self.assertNotIn('Path("${INITIAL_STABLE_VERDICT}")', self.signing)

    def test_direct_script_invocations_can_import_repository_package(self) -> None:
        self.assertIn("PYTHONPATH: ${{ github.workspace }}", self.signing)

    def test_assurance_requires_runtime_run_exact_source_revision(self) -> None:
        self.assertIn('SOURCE_SHA="$GITHUB_SHA"', self.assurance)
        self.assertIn('.head_sha == $source', self.assurance)
        self.assertIn('test "$RUN_HEAD_SHA" = "$SOURCE_SHA"', self.assurance)
        self.assertIn("runtime-workflow-head-sha.txt", self.assurance)
        self.assertIn("per_page=100", self.assurance)

    def test_signing_requires_assurance_run_exact_source_revision(self) -> None:
        self.assertIn(
            'TRIGGER_HEAD_SHA: ${{ github.event.workflow_run.head_sha }}',
            self.signing,
        )
        self.assertIn('.head_sha == $source', self.signing)
        self.assertIn('test "$RUN_HEAD_SHA" = "$SOURCE_SHA"', self.signing)
        self.assertIn('ref: ${{ steps.resolve.outputs.source_sha }}', self.signing)
        self.assertIn('--source-sha "$SOURCE_SHA"', self.signing)
        self.assertIn("assurance-run-head-sha.txt", self.signing)

    def test_signing_crosschecks_runtime_producer_revision(self) -> None:
        self.assertIn("runtime-workflow-head-sha.txt", self.signing)
        self.assertIn('= "$SOURCE_SHA"', self.signing)

    def test_signing_subject_source_revision_is_explicit_and_exact(self) -> None:
        revision = "a" * 40
        self.assertEqual(SUBJECT_BUILDER._source_revision(revision), revision)
        for invalid in ("", "a" * 39, "A" * 40, "g" * 40):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AssuranceError) as raised:
                    SUBJECT_BUILDER._source_revision(invalid)
                self.assertEqual(raised.exception.code, "INVALID_SOURCE_REVISION")
        self.assertNotIn('os.environ.get("GITHUB_SHA"', self.subject_builder)

    def test_signing_subject_consumes_resolver_lock_digest(self) -> None:
        lock = self._resolved_lock()
        self.assertEqual(
            SUBJECT_BUILDER._distribution_lock_identity(lock),
            lock["lock_digest"],
        )

    def test_signing_subject_rejects_tampered_lock_digest(self) -> None:
        lock = self._resolved_lock()
        lock["lock_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_DIGEST_MISMATCH")

    def test_signing_subject_rejects_legacy_id_fallback(self) -> None:
        lock = self._resolved_lock()
        lock["id"] = lock.pop("lock_digest")
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_DIGEST_MISSING")

    def test_signing_subject_rejects_receipt_binding_mismatch(self) -> None:
        lock = deepcopy(self._resolved_lock())
        lock["receipt"]["subject"]["digest"]["sha256"] = "0" * 64
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_RECEIPT_BINDING_MISMATCH")

    def test_workflows_watch_this_contract_test(self) -> None:
        watched_path = '"tests/test_keyless_signing_workflow_contract.py"'
        self.assertGreaterEqual(self.signing.count(watched_path), 2)
        self.assertGreaterEqual(self.assurance.count(watched_path), 2)


if __name__ == "__main__":
    unittest.main()
