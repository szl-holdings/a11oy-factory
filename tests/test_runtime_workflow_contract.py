import unittest
from pathlib import Path


class RuntimeWorkflowContractTests(unittest.TestCase):
    def test_runtime_workflow_executes_only_after_merge(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/vllm-cpu-runtime-execution.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: vllm-cpu-runtime-execution", workflow)
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertIn("--component pytorch-cpu-amd64", workflow)
        self.assertIn("--component vllm-cpu-amd64", workflow)
        self.assertIn("scripts/run_vllm_cpu_smoke.py", workflow)
        self.assertIn("runtime_execution_verified", workflow)
        self.assertIn("production_runtime_certified", workflow)
        self.assertIn("a11oy-vllm-cpu-amd64-runtime-proof", workflow)
        self.assertIn("Runtime execution gate", workflow)

    def test_runtime_proof_does_not_claim_production_certification(self):
        root = Path(__file__).resolve().parents[1]
        executor = (root / "scripts/run_vllm_cpu_smoke.py").read_text(encoding="utf-8")
        self.assertIn('"runtime_execution_verified": True', executor)
        self.assertIn('"production_runtime_certified": False', executor)
        self.assertIn('importlib.import_module("vllm._C")', executor)
        self.assertIn("llm.generate", executor)


if __name__ == "__main__":
    unittest.main()
