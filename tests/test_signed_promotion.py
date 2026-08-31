import hashlib
import unittest

from a11oy_factory.assurance import (
    ASSURANCE_POLICY_SCHEMA,
    ASSURANCE_SCAN_SCHEMA,
    AssuranceError,
    digest_json,
    evaluate_assurance,
)
from a11oy_factory.signed_promotion import (
    SIGSTORE_PROOF_SCHEMA,
    SIGNED_PROMOTION_SCHEMA,
    SIGNING_SUBJECT_SCHEMA,
    canonical_bytes,
    finalize_stable_verdict,
    verify_signed_promotion,
)


class SignedPromotionTests(unittest.TestCase):
    def _scan(self, vulnerabilities=None):
        vulnerabilities = list(vulnerabilities or [])
        return {
            "schema": ASSURANCE_SCAN_SCHEMA,
            "ok": True,
            "decision": "OBSERVED",
            "packages": [
                {
                    "name": "example",
                    "version": "1.0.0",
                    "license_expression": "Apache-2.0",
                    "license": None,
                    "license_classifiers": [],
                    "license_files": [
                        {"path": "LICENSE", "size": 1, "sha256": "a" * 64}
                    ],
                    "download_hashes": {"sha256": "b" * 64},
                }
            ],
            "osv": {"complete": True},
            "vulnerabilities": vulnerabilities,
            "counts": {
                "packages": 1,
                "vulnerabilities": len(vulnerabilities),
            },
        }

    def _runtime(self):
        return {
            "runtime_execution_verified": True,
            "production_runtime_certified": False,
            "signer": "UNSIGNED-honest",
            "proof_sha256": "c" * 64,
        }

    def _policy(self):
        return {
            "schema": ASSURANCE_POLICY_SCHEMA,
            "id": "stable-v1",
            "channel": "stable",
            "block_severities": ["HIGH", "CRITICAL"],
            "block_unknown_severity": True,
            "minimum_license_status": "DECLARED",
            "require_osv_complete": True,
            "require_runtime_execution": True,
            "require_production_runtime_certification": False,
            "require_cryptographic_signature": True,
            "require_download_hashes": True,
        }

    def _initial(self, vulnerabilities=None):
        return evaluate_assurance(
            self._scan(vulnerabilities),
            self._runtime(),
            self._policy(),
        )

    def _subject(self, initial):
        body = {
            "schema": SIGNING_SUBJECT_SCHEMA,
            "repository": "szl-holdings/a11oy-factory",
            "commit_sha": "1" * 40,
            "ref": "refs/heads/main",
            "workflow_ref": (
                "szl-holdings/a11oy-factory/.github/workflows/"
                "factory-keyless-signing.yml@refs/heads/main"
            ),
            "scan_sha256": initial["scan_sha256"],
            "runtime_proof_sha256": initial["runtime_proof_sha256"],
            "distribution_lock_sha256": "d" * 64,
            "distribution_lock_id": "sha256:" + "e" * 64,
            "initial_stable_verdict_sha256": initial["proof_sha256"],
            "stable_policy_sha256": "f" * 64,
            "stable_policy_id": "stable-v1",
            "evidence_files": {},
            "assurance": {
                "runtime_execution_verified": True,
                "production_runtime_certified": False,
                "initial_stable_decision": initial["decision"],
                "signature_state_before_signing": "UNSIGNED-honest",
            },
        }
        body["proof_sha256"] = digest_json(body)
        return body

    def _proof(self, subject, *, issuer="https://token.actions.githubusercontent.com"):
        body = {
            "schema": SIGSTORE_PROOF_SCHEMA,
            "verified": True,
            "signer": "SIGSTORE-keyless",
            "certificate_identity": (
                "https://github.com/szl-holdings/a11oy-factory/.github/workflows/"
                "factory-keyless-signing.yml@refs/heads/main"
            ),
            "certificate_oidc_issuer": issuer,
            "subject_sha256": hashlib.sha256(canonical_bytes(subject)).hexdigest(),
            "subject_proof_sha256": subject["proof_sha256"],
            "bundle_sha256": "9" * 64,
            "cosign_binary_sha256": "8" * 64,
            "cosign_version": "GitVersion: v2.4.1",
            "transparency_log_verified": True,
            "transparency_material_embedded": True,
            "repository": "szl-holdings/a11oy-factory",
            "workflow": "factory-keyless-signing",
            "workflow_ref": subject["workflow_ref"],
            "run_id": "123",
            "run_attempt": "1",
            "commit_sha": subject["commit_sha"],
            "verification": {
                "method": "cosign verify-blob",
                "certificate_identity_exact": True,
                "certificate_oidc_issuer_exact": True,
                "offline": False,
            },
            "honesty": {
                "signature_binds_subject_only": True,
                "signature_does_not_certify_runtime": True,
                "signature_does_not_clear_vulnerabilities": True,
            },
        }
        body["proof_sha256"] = digest_json(body)
        return body

    def test_verified_signature_resolves_only_signature_blocker(self):
        initial = self._initial()
        self.assertEqual(initial["decision"], "BLOCKED")
        self.assertEqual(
            [issue["code"] for issue in initial["issues"]],
            ["CRYPTOGRAPHIC_SIGNATURE_REQUIRED"],
        )
        subject = self._subject(initial)
        final = finalize_stable_verdict(initial, subject, self._proof(subject))
        self.assertEqual(final["schema"], SIGNED_PROMOTION_SCHEMA)
        self.assertTrue(final["ok"])
        self.assertEqual(final["decision"], "ALLOW")
        self.assertEqual(final["signer"], "SIGSTORE-keyless")
        self.assertTrue(final["cryptographic_signature"])
        self.assertTrue(final["transparency_log_verified"])
        self.assertFalse(final["production_runtime_certified"])
        self.assertEqual(final["issues"], [])
        self.assertTrue(verify_signed_promotion(final))

    def test_signature_does_not_erase_vulnerability_failure(self):
        vulnerability = {
            "id": "OSV-TEST-1",
            "package": "example",
            "version": "1.0.0",
            "severity": "CRITICAL",
            "summary": "test",
        }
        initial = self._initial([vulnerability])
        subject = self._subject(initial)
        final = finalize_stable_verdict(initial, subject, self._proof(subject))
        self.assertFalse(final["ok"])
        self.assertEqual(final["decision"], "BLOCKED")
        self.assertTrue(final["cryptographic_signature"])
        self.assertEqual(final["counts"]["resolved_signature_issues"], 1)
        self.assertEqual(final["counts"]["remaining_issues"], 1)
        self.assertEqual(final["issues"][0]["code"], "BLOCKED_VULNERABILITIES")
        self.assertTrue(verify_signed_promotion(final))

    def test_wrong_oidc_issuer_is_rejected(self):
        initial = self._initial()
        subject = self._subject(initial)
        with self.assertRaises(AssuranceError):
            finalize_stable_verdict(
                initial,
                subject,
                self._proof(subject, issuer="https://example.invalid"),
            )

    def test_subject_binding_mismatch_is_rejected(self):
        initial = self._initial()
        subject = self._subject(initial)
        subject["scan_sha256"] = "0" * 64
        subject["proof_sha256"] = digest_json(
            {key: value for key, value in subject.items() if key != "proof_sha256"}
        )
        with self.assertRaises(AssuranceError):
            finalize_stable_verdict(initial, subject, self._proof(subject))

    def test_signed_verdict_tamper_is_detected(self):
        initial = self._initial()
        subject = self._subject(initial)
        final = finalize_stable_verdict(initial, subject, self._proof(subject))
        final["decision"] = "BLOCKED"
        self.assertFalse(verify_signed_promotion(final))


if __name__ == "__main__":
    unittest.main()
