import copy
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from a11oy_factory.assurance import ASSURANCE_SCAN_SCHEMA, evaluate_assurance


SPEC = importlib.util.spec_from_file_location(
    "python_environment_scan", Path(__file__).resolve().parents[1] / "scripts/scan_python_environment.py"
)
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)
ENDPOINT = "https://api.osv.dev/v1/querybatch"
STAMP = "2026-10-13T00:00:00Z"


def package(name="alpha"):
    return {"name": name, "version": "1.0", "osv_version": "1.0"}


def detail(identifier="GHSA-test-aaaa-bbbb", **extra):
    return {"id": identifier, "modified": STAMP, "affected": [], **extra}


def summary(identifier="GHSA-test-aaaa-bbbb"):
    return {"id": identifier, "modified": STAMP}


class PythonEnvironmentScanTests(unittest.TestCase):
    def run_query(self, packages=None):
        return scanner._query_osv(packages or [package()], endpoint=ENDPOINT, timeout=1.0, retries=1)

    def test_id_only_batch_is_hydrated_before_severity_and_references(self):
        record = detail(database_specific={"severity": "HIGH"}, aliases=["CVE-2026-12345"],
                        references=[{"url": "https://osv.dev/test"}], summary="A real advisory")
        with patch.object(scanner, "_post_json", return_value={"results": [{"vulns": [summary()]}]}), \
             patch.object(scanner, "_get_json", return_value=record) as get:
            rows, meta = self.run_query()
        self.assertTrue(meta["complete"])
        self.assertEqual(rows[0]["severity"], "HIGH")
        self.assertEqual(rows[0]["aliases"], ["CVE-2026-12345"])
        self.assertEqual(rows[0]["references"], ["https://osv.dev/test"])
        self.assertEqual(rows[0]["summary"], "A real advisory")
        self.assertEqual(get.call_count, 1)
        self.assertEqual(get.call_args.args[0], "https://api.osv.dev/v1/vulns/GHSA-test-aaaa-bbbb")

    def test_shared_id_is_fetched_once_but_keeps_each_package(self):
        with patch.object(scanner, "_post_json", return_value={"results": [
            {"vulns": [summary(), summary()]}, {"vulns": [summary()]}
        ]}), patch.object(scanner, "_get_json", return_value=detail()) as get:
            rows, _ = self.run_query([package("alpha"), package("beta")])
        self.assertEqual([r["package"] for r in rows], ["alpha", "beta"])
        self.assertEqual(get.call_count, 1)
        self.assertEqual({r["severity"] for r in rows}, {"UNKNOWN"})

    def test_withdrawn_detail_is_ignored(self):
        withdrawn = {"id": summary()["id"], "modified": STAMP, "withdrawn": STAMP}
        with patch.object(scanner, "_post_json", return_value={"results": [{"vulns": [summary()]}]}), \
             patch.object(scanner, "_get_json", return_value=withdrawn):
            rows, meta = self.run_query()
        self.assertEqual(rows, [])
        self.assertEqual(meta["withdrawn_matches_ignored"], 1)
        self.assertTrue(meta["complete"])

    def test_severity_is_scoped_to_matching_pypi_package(self):
        record = detail(affected=[
            {"package": {"ecosystem": "PyPI", "name": "Alpha_Package"},
             "severity": [{"type": "CVSS_V3", "score": "9.8"}],
             "database_specific": {"severity": "LOW"}},
            {"package": {"ecosystem": "PyPI", "name": "beta"},
             "ecosystem_specific": {"severity": "HIGH"}},
            {"package": {"ecosystem": "npm", "name": "gamma"},
             "ecosystem_specific": {"severity": "CRITICAL"}},
        ])
        with patch.object(scanner, "_post_json", return_value={"results": [
            {"vulns": [summary()]}, {"vulns": [summary()]}, {"vulns": [summary()]}
        ]}), patch.object(scanner, "_get_json", return_value=record) as get:
            rows, _ = self.run_query([package("alpha-package"), package("beta"), package("gamma")])
        observed = {row["package"]: row for row in rows}
        self.assertEqual(observed["alpha-package"]["severity"], "CRITICAL")
        self.assertEqual(observed["alpha-package"]["severity_score"], 9.8)
        self.assertEqual(observed["alpha-package"]["severity_source"], "affected[0].CVSS_V3")
        self.assertEqual(observed["beta"]["severity"], "HIGH")
        self.assertEqual(observed["gamma"]["severity"], "UNKNOWN")
        self.assertEqual(get.call_count, 1)
        policy = json.loads((Path(__file__).resolve().parents[1] /
                             "factory/policy/assurance-candidate.json").read_text())
        scan = {"schema": ASSURANCE_SCAN_SCHEMA, "osv": {"complete": True},
                "packages": [{"name": name, "version": "1.0", "license_expression": "MIT",
                              "download_hashes": {"sha256": "a" * 64}}
                             for name in observed], "vulnerabilities": []}
        runtime = {"runtime_execution_verified": True, "production_runtime_certified": False}
        self.assertEqual(evaluate_assurance(scan, runtime, policy)["decision"], "ALLOW")
        scan["vulnerabilities"] = rows
        verdict = evaluate_assurance(scan, runtime, policy)
        self.assertEqual(verdict["decision"], "BLOCKED")
        self.assertEqual(verdict["counts"]["blocked_vulnerabilities"], 1)

    def test_matching_critical_severity_cannot_be_masked_by_other_fields(self):
        record = detail(database_specific={"severity": "LOW"}, affected=[
            {"package": {"ecosystem": "PyPI", "name": "alpha"},
             "ecosystem_specific": {"severity": "CRITICAL"}},
            {"package": {"ecosystem": "PyPI", "name": "alpha"},
             "ecosystem_specific": {"severity": "LOW"}},
        ])
        self.assertEqual(scanner._package_severity(record, "alpha")["label"], "CRITICAL")
        record["severity"] = [{"type": "CVSS_V3", "score": "9.9"}]
        self.assertEqual(scanner._package_severity(record, "alpha")["score"], 9.9)

    def test_empty_result_is_complete_without_details(self):
        with patch.object(scanner, "_post_json", return_value={"results": [{}]}), \
             patch.object(scanner, "_get_json") as get:
            rows, meta = self.run_query()
        self.assertEqual(rows, [])
        self.assertTrue(meta["complete"])
        get.assert_not_called()

    def test_partial_pagination_preserves_original_package_binding(self):
        one, two = "GHSA-one-aaaa-bbbb", "GHSA-two-aaaa-bbbb"
        responses = [
            {"results": [{}, {"next_page_token": "page-2"}]},
            {"results": [{"vulns": [summary(one)], "next_page_token": "page-3"}]},
            {"results": [{"vulns": [summary(two)]}]},
        ]
        calls = []
        def post(url, payload, timeout):
            calls.append(copy.deepcopy(payload))
            return responses.pop(0)
        def get(url, timeout):
            return detail(url.rsplit("/", 1)[-1])
        with patch.object(scanner, "_post_json", side_effect=post), patch.object(scanner, "_get_json", side_effect=get):
            rows, meta = self.run_query([package("alpha"), package("beta")])
        self.assertEqual({r["package"] for r in rows}, {"beta"})
        self.assertEqual({r["id"] for r in rows}, {one, two})
        self.assertTrue(meta["complete"])
        self.assertEqual(len(calls[1]["queries"]), 1)
        self.assertEqual(calls[1]["queries"][0]["package"]["name"], "beta")
        self.assertEqual(calls[1]["queries"][0]["page_token"], "page-2")
        self.assertEqual(calls[2]["queries"][0]["page_token"], "page-3")

    def test_detail_error_or_malformed_record_never_claims_complete(self):
        invalid = [None, [], {}, detail("GHSA-wrong-aaaa-bbbb"),
                   {"id": summary()["id"], "modified": STAMP}, detail(modified=""), detail(affected={}),
                   detail(modified="not-a-date"), detail(withdrawn=True), detail(withdrawn="not-a-date"),
                   detail(aliases="CVE-not-an-array"), detail(references=["not-an-object"])]
        for response in invalid:
            with self.subTest(response=response), \
                 patch.object(scanner, "_post_json", return_value={"results": [{"vulns": [summary()]}]}), \
                 patch.object(scanner, "_get_json", return_value=response):
                with self.assertRaises((RuntimeError, ValueError)):
                    self.run_query()
        with patch.object(scanner, "_post_json", return_value={"results": [{"vulns": [summary()]}]}), \
             patch.object(scanner, "_get_json", side_effect=OSError("unavailable")):
            with self.assertRaises(RuntimeError):
                self.run_query()

    def test_malformed_batch_is_not_silently_treated_as_zero_hits(self):
        for result in [None, [], {"vulns": {}}, {"vulns": [None]}, {"vulns": [{}]},
                       {"vulns": [{"id": 7}]}, {"next_page_token": []}]:
            with self.subTest(result=result), patch.object(scanner, "_post_json", return_value={"results": [result]}), \
                 patch.object(scanner, "_get_json", return_value=detail()):
                with self.assertRaises((RuntimeError, ValueError)):
                    self.run_query()

    def test_repeating_page_token_fails_closed(self):
        with patch.object(scanner, "_post_json", return_value={"results": [{"next_page_token": "same"}]}):
            with self.assertRaises(RuntimeError):
                self.run_query()

    def test_finite_positive_timeout_is_required(self):
        for timeout in [0, -1, float("nan"), float("inf")]:
            with self.subTest(timeout=timeout), patch.object(scanner, "_post_json") as post:
                with self.assertRaises((RuntimeError, ValueError)):
                    scanner._query_osv([package()], endpoint=ENDPOINT, timeout=timeout, retries=1)
                post.assert_not_called()

    def test_budget_exhaustion_is_not_a_complete_scan(self):
        for limit, value, result in [
            ("_MAX_OSV_DETAILS", 0, {"vulns": [summary()]}),
            ("_MAX_OSV_PAGES", 1, {"next_page_token": "next"}),
            ("_MAX_OSV_REQUESTS", 1, {"vulns": [summary()]}),
        ]:
            with self.subTest(limit=limit), patch.object(scanner, limit, value), \
                 patch.object(scanner, "_post_json", return_value={"results": [result]}), \
                 patch.object(scanner, "_get_json", return_value=detail()):
                with self.assertRaises(RuntimeError):
                    self.run_query()

    def test_transport_bounds_response_bytes_and_requires_json_object(self):
        for raw in [b"x" * 33, b"not json", b"[]", b"null"]:
            with self.subTest(raw=raw), patch.object(scanner, "_MAX_OSV_RESPONSE_BYTES", 32):
                response = io.BytesIO(raw)
                response.status = 200
                with patch.object(scanner.urllib.request, "urlopen", return_value=response):
                    with self.assertRaises((RuntimeError, ValueError)):
                        scanner._request_json(ENDPOINT, None, 1.0)
        response = io.BytesIO(b'{"ok":true}')
        response.status = 200
        with patch.object(scanner.urllib.request, "urlopen", return_value=response) as opened:
            self.assertEqual(scanner._request_json(ENDPOINT, None, 1.0), {"ok": True})
        self.assertEqual(opened.call_args.args[0].method, "GET")

    def test_transient_detail_failure_retries_then_hydrates(self):
        with patch.object(scanner, "_post_json", return_value={"results": [{"vulns": [summary()]}]}), \
             patch.object(scanner, "_get_json", side_effect=[OSError("temporary"), detail()]) as get, \
             patch.object(scanner.time, "sleep") as sleep:
            rows, meta = scanner._query_osv([package()], endpoint=ENDPOINT, timeout=1.0, retries=2)
        self.assertEqual(len(rows), 1)
        self.assertTrue(meta["complete"])
        self.assertEqual(get.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    def test_exhausted_transport_retries_are_bounded(self):
        with patch.object(scanner, "_post_json", side_effect=OSError("unavailable")) as post, \
             patch.object(scanner.time, "sleep"):
            with self.assertRaises(RuntimeError):
                scanner._query_osv([package()], endpoint=ENDPOINT, timeout=1.0, retries=999)
        self.assertEqual(post.call_count, 4)

    def test_deadline_exhaustion_prevents_network_and_complete_result(self):
        with patch.object(scanner.time, "monotonic", side_effect=[0.0, 301.0]), \
             patch.object(scanner, "_post_json") as post:
            with self.assertRaises(RuntimeError):
                self.run_query()
        post.assert_not_called()
        with patch.object(scanner.time, "monotonic", side_effect=[0.0, 1.0, 301.0]), \
             patch.object(scanner, "_post_json", return_value={"results": [{}]}):
            with self.assertRaises(RuntimeError):
                self.run_query()


if __name__ == "__main__":
    unittest.main()
