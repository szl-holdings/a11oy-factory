import importlib.util
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


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

    def test_provider_revision_must_match_this_upload(self):
        verifier._assert_provider_revision(SimpleNamespace(sha="b" * 40), "b" * 40)
        for observed, expected in (("c" * 40, "b" * 40), (None, "b" * 40), ("b" * 40, "")):
            with self.subTest(observed=observed, expected=expected):
                with self.assertRaises(verifier.TerminalSpaceError):
                    verifier._assert_provider_revision(SimpleNamespace(sha=observed), expected)

    def test_provider_write_during_endpoint_probes_blocks_receipt(self):
        health, distribution = self.valid_contract()
        api = Mock()
        api.get_space_runtime.return_value = SimpleNamespace(stage="RUNNING")
        api.space_info.side_effect = [
            SimpleNamespace(sha="b" * 40, host=verifier.SPACE_ORIGIN),
            SimpleNamespace(sha="c" * 40, host=verifier.SPACE_ORIGIN),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "deployment.json"
            with (
                patch.dict(os.environ, {
                    "HF_TOKEN": "test-token",
                    "FACTORY_SOURCE_SHA": "a" * 40,
                    "FACTORY_PROVIDER_SHA": "b" * 40,
                    "HF_VERIFY_OUTPUT": str(output),
                    "HF_VERIFY_INITIAL_DELAY": "0",
                    "HF_VERIFY_TIMEOUT": "1",
                }),
                patch.object(verifier, "HfApi", return_value=api),
                patch.object(verifier, "_get_json", side_effect=[health, distribution]),
                patch.object(verifier, "_current_main_sha", return_value="a" * 40),
            ):
                result = verifier.main()
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("revision does not match", payload["error"])

    def test_private_space_probe_authenticates_only_to_configured_origin(self):
        response = io.BytesIO(b'{"ok": true}')
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        opener = Mock()
        opener.open.return_value = response
        with patch.object(verifier.urllib.request, "build_opener", return_value=opener):
            result = verifier._get_json(verifier.SPACE_ORIGIN, "/healthz", token="test-token")
        self.assertTrue(result["ok"])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        with patch.object(verifier.urllib.request, "build_opener") as build:
            with self.assertRaises(verifier.TerminalSpaceError):
                verifier._get_json("https://example.invalid", "/healthz", token="test-token")
            build.assert_not_called()

    def test_private_space_probe_never_forwards_credentials_on_redirect(self):
        with self.assertRaisesRegex(RuntimeError, "redirected"):
            verifier._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid")

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
