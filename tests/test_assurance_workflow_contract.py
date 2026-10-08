import os
import re
import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path


class AssuranceWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_scheduled_and_calls_exact_runtime_proof(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (
            root / ".github/workflows/factory-supply-chain-assurance.yml"
        ).read_text(encoding="utf-8")
        runtime_workflow = (
            root / ".github/workflows/vllm-cpu-runtime-execution.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("name: factory-supply-chain-assurance", workflow)
        self.assertIn('cron: "23 6 * * 1"', workflow)
        self.assertIn("permissions:", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("scan_python_environment.py", workflow)
        self.assertIn("https://api.osv.dev/v1/querybatch", (
            root / "a11oy_factory/assurance.py"
        ).read_text(encoding="utf-8"))
        self.assertIn("workflow_call:", runtime_workflow)
        self.assertIn("uses: ./.github/workflows/vllm-cpu-runtime-execution.yml", workflow)
        self.assertIn("needs: [contract, runtime]", workflow)
        self.assertNotIn("vllm-cpu-runtime-execution.yml/runs", workflow)
        self.assertIn("name: a11oy-vllm-cpu-runtime-execution", runtime_workflow)
        self.assertIn("dist/runtime/runtime-execution.json", runtime_workflow)
        self.assertIn("artifact-ids: ${{ needs.runtime.outputs.artifact_id }}", workflow)
        self.assertIn("verify_runtime_proof_binding.py", workflow)
        self.assertIn("RUNTIME_RESULT: ${{ needs.runtime.result }}", workflow)
        self.assertIn("dist/assurance/runtime/runtime-execution.json", workflow)
        self.assertIn("CRYPTOGRAPHIC_SIGNATURE_REQUIRED", workflow)
        self.assertIn("a11oy-factory-supply-chain-assurance", workflow)

    def test_networked_observation_does_not_run_on_pull_requests(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (
            root / ".github/workflows/factory-supply-chain-assurance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertIn("Supply-chain assurance gate", workflow)

    def test_gate_refuses_failed_or_skipped_runtime_execution(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/factory-supply-chain-assurance.yml").read_text(encoding="utf-8")
        gate = workflow.split("\n  gate:\n", 1)[1]
        match = re.search(r"        run: \|\n((?:          .*\n|\n)+)", gate)
        self.assertIsNotNone(match)
        assert match is not None
        script = textwrap.dedent(match.group(1))
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        bash = str(git_bash) if git_bash.is_file() else shutil.which("bash")
        if bash is None:
            self.skipTest("Bash unavailable for workflow gate replay")
        for event, contract, runtime, observe, allowed in (
            ("schedule", "success", "success", "success", True),
            ("workflow_dispatch", "success", "failure", "skipped", False),
            ("push", "success", "skipped", "success", False),
            ("push", "failure", "success", "success", False),
            ("pull_request", "success", "skipped", "skipped", True),
            ("pull_request", "success", "success", "skipped", False),
        ):
            with self.subTest(event=event, runtime=runtime, contract=contract):
                environment = {
                    **os.environ,
                    "EVENT_NAME": event,
                    "CONTRACT_RESULT": contract,
                    "RUNTIME_RESULT": runtime,
                    "OBSERVE_RESULT": observe,
                }
                result = subprocess.run([bash, "-c", script], env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, allowed, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
