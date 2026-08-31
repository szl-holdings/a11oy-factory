import hashlib
import io
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from a11oy_factory.distribution import (
    FactoryError,
    build_plan,
    canonical_bytes,
    catalog_summary,
    generate_provenance,
    generate_spdx,
    materialize_artifacts,
    read_json,
    resolve_distribution,
    verify_distribution,
    write_bundle,
)


def fixture():
    payload = b"trusted-ai-artifact\n"
    digest = hashlib.sha256(payload).hexdigest()
    catalog = {
        "schema": "a11oy.factory.catalog/v1",
        "name": "test catalog",
        "targets": {
            "linux-amd64-cpu": {
                "os": "linux",
                "arch": "amd64",
                "accelerator": "cpu",
                "python": "3.12",
            }
        },
        "policy_defaults": {
            "allowed_licenses": ["Apache-2.0"],
            "allowed_source_hosts": ["example.com"],
            "require_immutable_sources": True,
            "required_evidence_types": ["release-asset-digest"],
            "permitted_vulnerability_status": ["UNVERIFIED"],
            "allow_network_builds": False,
            "max_components": 8,
            "max_artifact_bytes": 1024,
        },
        "components": [
            {
                "id": "runtime",
                "version": "1.0.0",
                "kind": "runtime",
                "license": "Apache-2.0",
                "supplier": "Example",
                "description": "Pinned runtime.",
                "targets": ["linux-amd64-cpu"],
                "requires": [],
                "source": {
                    "type": "artifact",
                    "uri": "https://example.com/runtime.bin",
                    "filename": "runtime.bin",
                    "digest": f"sha256:{digest}",
                    "size": len(payload),
                },
                "evidence": [
                    {
                        "type": "release-asset-digest",
                        "uri": "https://example.com/releases/1.0.0",
                    }
                ],
                "vulnerability": {
                    "status": "UNVERIFIED",
                    "scanner": None,
                    "observed_at": None,
                },
                "build": {"network": False, "steps": []},
            },
            {
                "id": "server",
                "version": "2.0.0",
                "kind": "server",
                "license": "Apache-2.0",
                "supplier": "Example",
                "description": "Pinned server.",
                "targets": ["linux-amd64-cpu"],
                "requires": ["runtime"],
                "source": {
                    "type": "git",
                    "uri": "https://example.com/server.git",
                    "revision": "a" * 40,
                },
                "evidence": [
                    {
                        "type": "release-asset-digest",
                        "uri": "https://example.com/server/commit",
                    }
                ],
                "vulnerability": {
                    "status": "UNVERIFIED",
                    "scanner": None,
                    "observed_at": None,
                },
                "build": {
                    "network": False,
                    "steps": [
                        {
                            "name": "self-test",
                            "argv": ["python", "-m", "unittest"],
                        }
                    ],
                },
            },
        ],
    }
    profile = {
        "schema": "a11oy.factory.profile/v1",
        "id": "test-profile",
        "channel": "candidate",
        "assurance": "INTEGRITY_LOCKED",
        "target": "linux-amd64-cpu",
        "roots": ["server"],
        "source_date_epoch": 0,
        "policy": {},
    }
    return catalog, profile, payload


class DistributionTests(unittest.TestCase):
    def test_resolution_is_deterministic_and_dependency_first(self):
        catalog, profile, _ = fixture()
        first = resolve_distribution(catalog, profile)
        second = resolve_distribution(deepcopy(catalog), deepcopy(profile))
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(first["graph"]["order"], ["runtime", "server"])
        self.assertEqual(first["policy"]["decision"], "ALLOW")
        self.assertEqual(first["assurance"]["runtime"], "NOT_CERTIFIED")
        self.assertEqual(first["assurance"]["vulnerabilities"], "UNVERIFIED")
        self.assertEqual(first["receipt"]["decision"], "ALLOW")
        self.assertEqual(len(first["receipt"]["hash"]), 64)

    def test_summary_exposes_honesty(self):
        catalog, _, _ = fixture()
        summary = catalog_summary(catalog)
        self.assertEqual(summary["components"], 2)
        self.assertFalse(summary["runtime_certified"])
        self.assertEqual(summary["vulnerability"]["UNVERIFIED"], 2)

    def test_policy_blocks_mutable_source(self):
        catalog, profile, _ = fixture()
        catalog["components"][1]["source"]["revision"] = "main"
        with self.assertRaises(FactoryError) as raised:
            resolve_distribution(catalog, profile)
        self.assertEqual(raised.exception.code, "policy_blocked")
        codes = {
            finding["code"]
            for finding in raised.exception.details["findings"]
            if finding["level"] == "BLOCK"
        }
        self.assertIn("mutable_source", codes)

    def test_policy_blocks_denied_license(self):
        catalog, profile, _ = fixture()
        catalog["components"][1]["license"] = "GPL-3.0-only"
        with self.assertRaises(FactoryError) as raised:
            resolve_distribution(catalog, profile)
        self.assertEqual(raised.exception.code, "policy_blocked")

    def test_cycle_fails_closed(self):
        catalog, profile, _ = fixture()
        catalog["components"][0]["requires"] = ["server"]
        with self.assertRaises(FactoryError) as raised:
            resolve_distribution(catalog, profile)
        self.assertEqual(raised.exception.code, "dependency_cycle")
        self.assertEqual(raised.exception.details["cycle"], ["server", "runtime", "server"])

    def test_target_mismatch_fails_closed(self):
        catalog, profile, _ = fixture()
        catalog["components"][1]["targets"] = ["*"]
        catalog["components"][0]["targets"] = ["other"]
        catalog["targets"]["other"] = {
            "os": "linux",
            "arch": "arm64",
            "accelerator": "cpu",
            "python": "3.12",
        }
        with self.assertRaises(FactoryError) as raised:
            resolve_distribution(catalog, profile)
        self.assertEqual(raised.exception.code, "incompatible_target")

    def test_plan_sbom_provenance_and_verify(self):
        catalog, profile, _ = fixture()
        lock = resolve_distribution(catalog, profile)
        plan = build_plan(lock)
        sbom = generate_spdx(lock)
        provenance = generate_provenance(lock)
        self.assertEqual(plan["default_mode"], "PLAN_ONLY")
        self.assertTrue(any(step["action"] == "fetch" for step in plan["steps"]))
        self.assertEqual(sbom["spdxVersion"], "SPDX-2.3")
        self.assertEqual(provenance["predicateType"], "https://slsa.dev/provenance/v1")
        report = verify_distribution(catalog, profile, lock, sbom=sbom, provenance=provenance)
        self.assertTrue(report["ok"])

    def test_tampered_lock_is_blocked(self):
        catalog, profile, _ = fixture()
        lock = resolve_distribution(catalog, profile)
        lock["components"][0]["version"] = "tampered"
        report = verify_distribution(catalog, profile, lock)
        self.assertFalse(report["ok"])
        self.assertEqual(report["decision"], "BLOCKED")

    def test_bundle_round_trip(self):
        catalog, profile, _ = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            result = write_bundle(catalog, profile, tmp)
            self.assertTrue(result["ok"])
            expected = {
                "factory.lock.json",
                "factory.plan.json",
                "factory.spdx.json",
                "factory.provenance.json",
                "factory.verification.json",
                "SHA256SUMS",
            }
            self.assertEqual(set(result["files"]), expected)
            lock = read_json(Path(tmp) / "factory.lock.json")
            sbom = read_json(Path(tmp) / "factory.spdx.json")
            provenance = read_json(Path(tmp) / "factory.provenance.json")
            self.assertTrue(
                verify_distribution(
                    catalog,
                    profile,
                    lock,
                    sbom=sbom,
                    provenance=provenance,
                )["ok"]
            )

    def test_materializer_verifies_bytes_without_execution(self):
        catalog, profile, payload = fixture()
        lock = resolve_distribution(catalog, profile)

        class Response:
            def __init__(self, body):
                self.body = io.BytesIO(body)
                self.headers = {"Content-Length": str(len(body))}

            def read(self, size=-1):
                return self.body.read(size)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def opener(request, timeout):
            self.assertEqual(request.full_url, "https://example.com/runtime.bin")
            self.assertGreater(timeout, 0)
            return Response(payload)

        with tempfile.TemporaryDirectory() as tmp:
            result = materialize_artifacts(
                lock,
                tmp,
                component_ids=["runtime"],
                opener=opener,
            )
            self.assertEqual(result["artifacts"][0]["status"], "DOWNLOADED_VERIFIED")
            self.assertEqual((Path(tmp) / "runtime.bin").read_bytes(), payload)
            reused = materialize_artifacts(
                lock,
                tmp,
                component_ids=["runtime"],
                opener=opener,
            )
            self.assertEqual(reused["artifacts"][0]["status"], "REUSED_VERIFIED")

    def test_materializer_rejects_digest_mismatch(self):
        catalog, profile, payload = fixture()
        lock = resolve_distribution(catalog, profile)

        class Response:
            headers = {"Content-Length": str(len(payload))}

            def __init__(self):
                self.body = io.BytesIO(b"x" * len(payload))

            def read(self, size=-1):
                return self.body.read(size)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FactoryError) as raised:
                materialize_artifacts(
                    lock,
                    tmp,
                    component_ids=["runtime"],
                    opener=lambda request, timeout: Response(),
                )
            self.assertEqual(raised.exception.code, "materialize_digest_mismatch")
            self.assertFalse(any(Path(tmp).glob("*.partial")))


class RepositoryFixturesTests(unittest.TestCase):
    def test_checked_in_catalog_and_profiles_resolve(self):
        root = Path(__file__).resolve().parents[1]
        catalog = read_json(root / "factory" / "catalog.json")
        profile_paths = sorted((root / "factory" / "profiles").glob("*.json"))
        self.assertEqual(len(profile_paths), 5)
        for path in profile_paths:
            with self.subTest(profile=path.name):
                profile = read_json(path)
                lock = resolve_distribution(catalog, profile)
                self.assertEqual(lock["policy"]["decision"], "ALLOW")
                self.assertEqual(len(lock["components"]), 2)
                self.assertEqual(lock["assurance"]["vulnerabilities"], "UNVERIFIED")
                self.assertEqual(lock["assurance"]["runtime"], "NOT_CERTIFIED")


if __name__ == "__main__":
    unittest.main()
