import unittest
from pathlib import Path


class AssuranceWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_scheduled_and_uses_existing_runtime_proof(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (
            root / ".github/workflows/factory-supply-chain-assurance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("name: factory-supply-chain-assurance", workflow)
        self.assertIn('cron: "23 6 * * 1"', workflow)
        self.assertIn("permissions:", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("scan_python_environment.py", workflow)
        self.assertIn("https://api.osv.dev/v1/querybatch", (
            root / "a11oy_factory/assurance.py"
        ).read_text(encoding="utf-8"))
        self.assertIn("vllm-cpu-runtime-execution.yml/runs", workflow)
        self.assertIn("a11oy-vllm-cpu-amd64-runtime-proof", workflow)
        self.assertIn("CRYPTOGRAPHIC_SIGNATURE_REQUIRED", workflow)
        self.assertIn("a11oy-factory-supply-chain-assurance", workflow)

    def test_networked_observation_does_not_run_on_pull_requests(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (
            root / ".github/workflows/factory-supply-chain-assurance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertIn("Supply-chain assurance gate", workflow)


if __name__ == "__main__":
    unittest.main()
