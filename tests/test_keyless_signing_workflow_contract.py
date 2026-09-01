# Copyright 2026 SZL Holdings — SPDX-License-Identifier: Apache-2.0
"""Regression tests for the assurance-to-signing artifact contract."""

from pathlib import Path
import unittest

from a11oy_factory.assurance import AssuranceError
from scripts.build_assurance_signing_subject import _distribution_lock_identity


ROOT = Path(__file__).resolve().parents[1]
SIGNING_WORKFLOW = ROOT / ".github" / "workflows" / "factory-keyless-signing.yml"
ASSURANCE_WORKFLOW = ROOT / ".github" / "workflows" / "factory-supply-chain-assurance.yml"


class KeylessSigningWorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signing = SIGNING_WORKFLOW.read_text(encoding="utf-8")
        self.assurance = ASSURANCE_WORKFLOW.read_text(encoding="utf-8")

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

    def test_generated_factory_lock_digest_is_a_supported_identity(self) -> None:
        digest = "sha256:" + "a" * 64
        self.assertEqual(
            _distribution_lock_identity(
                {
                    "schema": "a11oy.factory.lock/v1",
                    "lock_digest": digest,
                }
            ),
            digest,
        )

    def test_missing_distribution_lock_identity_fails_closed(self) -> None:
        with self.assertRaises(AssuranceError) as raised:
            _distribution_lock_identity({"schema": "a11oy.factory.lock/v1"})
        self.assertEqual(raised.exception.code, "LOCK_ID_MISSING")

    def test_workflow_watches_this_contract_test(self) -> None:
        watched_path = '"tests/test_keyless_signing_workflow_contract.py"'
        self.assertGreaterEqual(self.signing.count(watched_path), 2)


if __name__ == "__main__":
    unittest.main()
