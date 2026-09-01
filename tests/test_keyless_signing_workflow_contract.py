# Copyright 2026 SZL Holdings — SPDX-License-Identifier: Apache-2.0
"""Regression tests for the assurance-to-signing artifact contract."""

from pathlib import Path
import unittest


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

    def test_workflow_watches_this_contract_test(self) -> None:
        watched_path = '"tests/test_keyless_signing_workflow_contract.py"'
        self.assertGreaterEqual(self.signing.count(watched_path), 2)


if __name__ == "__main__":
    unittest.main()
