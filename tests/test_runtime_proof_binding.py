import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "verify_runtime_proof_binding", ROOT / "scripts/verify_runtime_proof_binding.py"
)
assert module_spec is not None and module_spec.loader is not None
binding_verifier = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(binding_verifier)


class RuntimeProofBindingTests(unittest.TestCase):
    """Synthetic records exercise provenance rejection without executing a model."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.proof_path = Path(self.directory.name) / "runtime-execution.json"
        self.binding_path = Path(self.directory.name) / "runtime-workflow-binding.json"
        self.proof = {
            "schema": "a11oy.factory.runtime-execution/v1",
            "ok": True,
            "decision": "ALLOW",
            "runtime_execution_verified": True,
            "production_runtime_certified": False,
            "fixture": "SAMPLE; no inference executed",
        }
        self.expected = {
            "source_sha": "a" * 40,
            "run_id": "123",
            "run_attempt": "1",
        }
        self._write_proof()

    def _write_proof(self):
        body = {key: value for key, value in self.proof.items() if key != "proof_sha256"}
        canonical = json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        self.proof["proof_sha256"] = hashlib.sha256(canonical).hexdigest()
        self.proof_path.write_text(json.dumps(self.proof), encoding="utf-8")
        self.expected["proof_file_sha256"] = hashlib.sha256(self.proof_path.read_bytes()).hexdigest()
        self.binding = {
            "schema": binding_verifier.BINDING_SCHEMA,
            "source_sha": self.expected["source_sha"],
            "workflow_run_id": self.expected["run_id"],
            "workflow_run_attempt": self.expected["run_attempt"],
            "proof_file_sha256": self.expected["proof_file_sha256"],
        }
        self._write_binding()

    def _write_binding(self):
        self.binding_path.write_text(json.dumps(self.binding), encoding="utf-8")

    def _verify(self):
        return binding_verifier.verify_binding(self.proof_path, self.binding_path, **self.expected)

    def test_exact_source_and_caller_run_binding_is_accepted(self):
        self.assertEqual(self._verify(), self.binding)

    def test_missing_proof_fails_closed(self):
        self.proof_path.unlink()
        with self.assertRaises(FileNotFoundError):
            self._verify()

    def test_missing_binding_fails_closed(self):
        self.binding_path.unlink()
        with self.assertRaises(FileNotFoundError):
            self._verify()

    def test_stale_source_run_and_attempt_fail_closed(self):
        for key, stale in (
            ("source_sha", "b" * 40),
            ("workflow_run_id", "122"),
            ("workflow_run_attempt", "2"),
        ):
            with self.subTest(key=key):
                original = self.binding[key]
                self.binding[key] = stale
                self._write_binding()
                with self.assertRaisesRegex(ValueError, "exact source and caller run"):
                    self._verify()
                self.binding[key] = original

    def test_failed_or_unverified_proof_fails_even_with_valid_digests(self):
        for key, failed in (("ok", False), ("decision", "BLOCKED"), ("runtime_execution_verified", False)):
            with self.subTest(key=key):
                original = self.proof[key]
                self.proof[key] = failed
                self._write_proof()
                with self.assertRaisesRegex(ValueError, "unsuccessful"):
                    self._verify()
                self.proof[key] = original

    def test_production_certification_overclaim_is_rejected(self):
        self.proof["production_runtime_certified"] = True
        self._write_proof()
        with self.assertRaisesRegex(ValueError, "scoped certification"):
            self._verify()

    def test_tampered_proof_bytes_are_rejected(self):
        self.proof_path.write_bytes(self.proof_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "file bytes"):
            self._verify()

    def test_invalid_embedded_digest_is_rejected_even_when_file_binding_matches(self):
        self.proof["proof_sha256"] = "c" * 64
        self.proof_path.write_text(json.dumps(self.proof), encoding="utf-8")
        digest = hashlib.sha256(self.proof_path.read_bytes()).hexdigest()
        self.expected["proof_file_sha256"] = digest
        self.binding["proof_file_sha256"] = digest
        self._write_binding()
        with self.assertRaisesRegex(ValueError, "embedded digest"):
            self._verify()

    def test_duplicate_binding_members_are_rejected(self):
        text = self.binding_path.read_text(encoding="utf-8")
        self.binding_path.write_text(text[:-1] + ', "source_sha": "' + "b" * 40 + '"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON member"):
            self._verify()

    def test_missing_producer_digest_is_rejected(self):
        self.expected["proof_file_sha256"] = ""
        with self.assertRaisesRegex(ValueError, "absent or malformed"):
            self._verify()


if __name__ == "__main__":
    unittest.main()
