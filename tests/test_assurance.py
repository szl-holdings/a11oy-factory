import unittest

from a11oy_factory.assurance import (
    ASSURANCE_POLICY_SCHEMA,
    ASSURANCE_SCAN_SCHEMA,
    AssuranceError,
    cvss3_base_score,
    evaluate_assurance,
    license_status,
    score_to_severity,
    validate_policy,
    verify_verdict,
    vulnerability_severity,
)


class AssuranceTests(unittest.TestCase):
    def _scan(self, vulnerabilities=None, *, complete=True, package=None):
        package = package or {
            "name": "example",
            "version": "1.0.0",
            "license_expression": "Apache-2.0",
            "license": None,
            "license_classifiers": [],
            "license_files": [{"path": "LICENSE", "size": 1, "sha256": "a" * 64}],
            "download_hashes": {"sha256": "b" * 64},
        }
        vulnerabilities = list(vulnerabilities or [])
        return {
            "schema": ASSURANCE_SCAN_SCHEMA,
            "ok": True,
            "decision": "OBSERVED",
            "packages": [package],
            "osv": {"complete": complete},
            "vulnerabilities": vulnerabilities,
            "counts": {
                "packages": 1,
                "vulnerabilities": len(vulnerabilities),
            },
        }

    def _runtime(self, *, signer="UNSIGNED-honest", executed=True):
        return {
            "runtime_execution_verified": executed,
            "production_runtime_certified": False,
            "signer": signer,
            "proof_sha256": "c" * 64,
        }

    def _policy(self, **overrides):
        policy = {
            "schema": ASSURANCE_POLICY_SCHEMA,
            "id": "candidate-v1",
            "channel": "candidate",
            "block_severities": ["CRITICAL"],
            "block_unknown_severity": False,
            "minimum_license_status": "EVIDENCE_ONLY",
            "require_osv_complete": True,
            "require_runtime_execution": True,
            "require_production_runtime_certification": False,
            "require_cryptographic_signature": False,
            "require_download_hashes": True,
        }
        policy.update(overrides)
        return policy

    def test_cvss31_vector_is_scored(self):
        score = cvss3_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        self.assertEqual(score, 9.8)
        self.assertEqual(score_to_severity(score), "CRITICAL")

    def test_database_severity_precedes_vector(self):
        severity = vulnerability_severity(
            {
                "database_specific": {"severity": "high"},
                "severity": [
                    {
                        "type": "CVSS_V3",
                        "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    }
                ],
            }
        )
        self.assertEqual(severity["label"], "HIGH")
        self.assertEqual(severity["source"], "database_specific.severity")

    def test_license_evidence_levels(self):
        self.assertEqual(license_status({"license_expression": "MIT"}), "STRUCTURED")
        self.assertEqual(license_status({"license": "BSD-3-Clause"}), "DECLARED")
        self.assertEqual(license_status({"license_classifiers": ["OSI Approved"]}), "DECLARED")
        self.assertEqual(license_status({"license_files": [{"path": "LICENSE"}]}), "EVIDENCE_ONLY")
        self.assertEqual(license_status({}), "UNKNOWN")

    def test_candidate_allows_complete_clean_scoped_execution(self):
        verdict = evaluate_assurance(self._scan(), self._runtime(), self._policy())
        self.assertTrue(verdict["ok"])
        self.assertEqual(verdict["decision"], "ALLOW")
        self.assertTrue(verify_verdict(verdict))
        self.assertFalse(verdict["production_runtime_certified"])

    def test_critical_vulnerability_blocks_candidate(self):
        vulnerability = {
            "id": "OSV-TEST-1",
            "package": "example",
            "version": "1.0.0",
            "severity": "CRITICAL",
            "summary": "test",
        }
        verdict = evaluate_assurance(
            self._scan([vulnerability]),
            self._runtime(),
            self._policy(),
        )
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["decision"], "BLOCKED")
        self.assertEqual(verdict["counts"]["blocked_vulnerabilities"], 1)
        self.assertTrue(verify_verdict(verdict))

    def test_stable_requires_real_signature(self):
        verdict = evaluate_assurance(
            self._scan(),
            self._runtime(),
            self._policy(
                id="stable-v1",
                channel="stable",
                block_severities=["HIGH", "CRITICAL"],
                block_unknown_severity=True,
                minimum_license_status="DECLARED",
                require_cryptographic_signature=True,
            ),
        )
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["decision"], "BLOCKED")
        self.assertTrue(
            any(issue["code"] == "CRYPTOGRAPHIC_SIGNATURE_REQUIRED" for issue in verdict["issues"])
        )

    def test_incomplete_osv_and_missing_runtime_fail_closed(self):
        verdict = evaluate_assurance(
            self._scan(complete=False),
            self._runtime(executed=False),
            self._policy(),
        )
        codes = {issue["code"] for issue in verdict["issues"]}
        self.assertIn("OSV_INCOMPLETE", codes)
        self.assertIn("RUNTIME_NOT_EXECUTED", codes)
        self.assertEqual(verdict["decision"], "BLOCKED")

    def test_unknown_license_and_missing_hash_are_visible(self):
        package = {
            "name": "opaque",
            "version": "0.1.0",
            "license_files": [],
            "download_hashes": {},
        }
        verdict = evaluate_assurance(
            self._scan(package=package),
            self._runtime(),
            self._policy(),
        )
        codes = {issue["code"] for issue in verdict["issues"]}
        self.assertIn("LICENSE_EVIDENCE_BELOW_POLICY", codes)
        self.assertIn("DOWNLOAD_HASH_REQUIRED", codes)

    def test_verdict_tamper_is_detected(self):
        verdict = evaluate_assurance(self._scan(), self._runtime(), self._policy())
        verdict["decision"] = "BLOCKED"
        self.assertFalse(verify_verdict(verdict))

    def test_invalid_policy_is_rejected(self):
        with self.assertRaises(AssuranceError):
            validate_policy(self._policy(block_severities=["MADE_UP"]))


if __name__ == "__main__":
    unittest.main()
