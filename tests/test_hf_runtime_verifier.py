import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class _FakeHfApi:
    pass


_fake_hub = types.ModuleType("huggingface_hub")
_fake_hub.HfApi = _FakeHfApi
sys.modules.setdefault("huggingface_hub", _fake_hub)

_SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "verify_factory_space.py"
_SPEC = importlib.util.spec_from_file_location("verify_factory_space", _SCRIPT)
assert _SPEC and _SPEC.loader
verifier = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verifier)


class RuntimeVerifierTests(unittest.TestCase):
    def valid_contract(self):
        health = {
            "ok": True,
            "version": "0.6.0",
            "factory_core": {
                "state": "LIVE",
                "runtime_certified": False,
            },
            "source_provenance": {
                "schema": verifier.SOURCE_PROVENANCE_SCHEMA,
                "state": "BOUND",
                "github_repository": verifier.GITHUB_REPOSITORY,
                "github_source_sha": "a" * 40,
            },
        }
        profiles = [
            {"id": profile_id, "decision": "ALLOW"}
            for profile_id in sorted(verifier.EXPECTED_PROFILE_IDS)
        ]
        distribution = {
            "ok": True,
            "state": "LIVE",
            "runtime_certified": False,
            "profiles": profiles,
        }
        return health, distribution

    def test_host_normalization_accepts_host_or_subdomain(self):
        self.assertEqual(
            verifier._as_url(SimpleNamespace(host="factory.example", subdomain=None)),
            "https://factory.example",
        )
        self.assertEqual(
            verifier._as_url(SimpleNamespace(host=None, subdomain="factory")),
            "https://factory.hf.space",
        )
        self.assertEqual(
            verifier._as_url(SimpleNamespace(host="https://factory.hf.space/", subdomain=None)),
            "https://factory.hf.space",
        )

    def test_host_normalization_fails_closed_without_location(self):
        with self.assertRaises(RuntimeError):
            verifier._as_url(SimpleNamespace(host=None, subdomain=None))

    def test_runtime_payload_normalizes_enum_like_values(self):
        runtime = SimpleNamespace(
            stage=SimpleNamespace(value="RUNNING"),
            hardware=SimpleNamespace(value="cpu-basic"),
            requested_hardware=None,
            sleep_time=172800,
        )
        self.assertEqual(
            verifier._runtime_payload(runtime),
            {
                "stage": "RUNNING",
                "hardware": "cpu-basic",
                "requested_hardware": None,
                "sleep_time": 172800,
            },
        )

    def test_live_contract_is_accepted(self):
        health, distribution = self.valid_contract()
        verifier._assert_contract(
            health,
            distribution,
            expected_source_sha="a" * 40,
        )

    def test_runtime_source_must_match_authorized_git_sha(self):
        health, distribution = self.valid_contract()
        with self.assertRaisesRegex(RuntimeError, "source SHA"):
            verifier._assert_contract(
                health,
                distribution,
                expected_source_sha="b" * 40,
            )

    def test_wrong_profile_set_is_rejected(self):
        health, distribution = self.valid_contract()
        distribution["profiles"] = distribution["profiles"][:-1]
        with self.assertRaises(RuntimeError):
            verifier._assert_contract(health, distribution)

    def test_runtime_certification_cannot_be_inflated(self):
        health, distribution = self.valid_contract()
        health["factory_core"]["runtime_certified"] = True
        with self.assertRaises(RuntimeError):
            verifier._assert_contract(health, distribution)

    def test_terminal_stages_cover_build_and_runtime_failures(self):
        self.assertIn("BUILD_ERROR", verifier.TERMINAL_FAILURE_STAGES)
        self.assertIn("RUNTIME_ERROR", verifier.TERMINAL_FAILURE_STAGES)
        self.assertIn("NO_APP_FILE", verifier.TERMINAL_FAILURE_STAGES)
        self.assertIn("RUNNING", verifier.ENDPOINT_STAGES)
        self.assertIn("SLEEPING", verifier.ENDPOINT_STAGES)

    def test_blocked_verification_writes_a_sanitized_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "deployment.json"
            with patch.dict(
                os.environ,
                {"HF_VERIFY_OUTPUT": str(output)},
                clear=False,
            ):
                result = verifier._record_failure(
                    "runtime failed?token=super-secret",
                    {"endpoint_error": "https://example.invalid/?access_token=super-secret"},
                    "a" * 40,
                )

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(payload["github_source_sha"], "a" * 40)
        self.assertNotIn("super-secret", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
