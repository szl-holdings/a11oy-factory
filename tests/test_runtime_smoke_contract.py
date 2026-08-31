import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_vllm_cpu_smoke.py"
SPEC = ROOT / "factory" / "runtime" / "vllm-cpu-amd64-smoke.json"

module_spec = importlib.util.spec_from_file_location("run_vllm_cpu_smoke", SCRIPT)
assert module_spec is not None and module_spec.loader is not None
runtime_smoke = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(runtime_smoke)


class RuntimeSmokeContractTests(unittest.TestCase):
    def test_checked_in_contract_is_fully_pinned_and_honest(self):
        contract = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "a11oy.factory.runtime-smoke/v1")
        self.assertEqual(contract["target"], "linux-amd64-cpu")
        self.assertEqual(contract["runtime_component"], "vllm-cpu-amd64")
        self.assertEqual(contract["torch_component"], "pytorch-cpu-amd64")
        self.assertEqual(contract["expected_vllm_version"], "0.28.0")
        self.assertEqual(contract["expected_torch_version"], "2.13.0+cpu")
        self.assertEqual(
            contract["model"]["revision"],
            "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        )
        self.assertEqual(contract["model"]["license"], "Apache-2.0")
        self.assertFalse(contract["model"]["trust_remote_code"])
        self.assertIn("model.safetensors", contract["model"]["allow_patterns"])
        self.assertFalse(contract["assurance"]["production_runtime_certified"])
        self.assertEqual(
            set(contract["assurance"]["required"]),
            {
                "PINNED_TORCH_WHEEL",
                "PINNED_RUNTIME_WHEEL",
                "NATIVE_EXTENSION_IMPORT",
                "PINNED_MODEL_REVISION",
                "MODEL_FILE_SHA256",
                "CPU_TOKEN_GENERATION",
            },
        )

    def _materialization(self, directory: Path):
        contract = json.loads(SPEC.read_text(encoding="utf-8"))
        records = []
        for component, payload in (
            (contract["torch_component"], b"pinned-torch-wheel"),
            (contract["runtime_component"], b"pinned-vllm-wheel"),
        ):
            path = directory / f"{component}.whl"
            path.write_bytes(payload)
            records.append(
                {
                    "component": component,
                    "path": str(path),
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "origin_host": "example.com",
                    "final_host": "cdn.example.com",
                    "status": "DOWNLOADED_VERIFIED",
                }
            )
        return contract, {
            "schema": "a11oy.factory.materialization/v1",
            "ok": True,
            "decision": "ALLOW",
            "lock_digest": "sha256:" + "a" * 64,
            "receipt_hash": "sha256:" + "b" * 64,
            "artifacts": records,
        }

    def test_materialization_contract_requires_both_verified_wheels(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, materialization = self._materialization(Path(tmp))
            result = runtime_smoke._validate_contract(contract, materialization)
            self.assertEqual(result["vllm"]["component"], "vllm-cpu-amd64")
            self.assertEqual(result["torch"]["component"], "pytorch-cpu-amd64")
            self.assertEqual(
                result["materialization_receipt_hash"],
                materialization["receipt_hash"],
            )

    def test_missing_torch_wheel_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, materialization = self._materialization(Path(tmp))
            materialization["artifacts"] = [
                record
                for record in materialization["artifacts"]
                if record["component"] != contract["torch_component"]
            ]
            with self.assertRaisesRegex(RuntimeError, "requires exactly"):
                runtime_smoke._validate_contract(contract, materialization)

    def test_post_materialization_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, materialization = self._materialization(Path(tmp))
            record = next(
                item
                for item in materialization["artifacts"]
                if item["component"] == contract["runtime_component"]
            )
            Path(record["path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "changed after materialization"):
                runtime_smoke._validate_contract(contract, materialization)

    def test_unverified_status_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract, materialization = self._materialization(Path(tmp))
            materialization["artifacts"][0]["status"] = "DOWNLOADED_UNVERIFIED"
            with self.assertRaisesRegex(RuntimeError, "bytes were not verified"):
                runtime_smoke._validate_contract(contract, materialization)


if __name__ == "__main__":
    unittest.main()
