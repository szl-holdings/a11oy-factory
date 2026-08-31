import io
import tempfile
import unittest
from pathlib import Path

from a11oy_factory.distribution import FactoryError, materialize_artifacts, resolve_distribution
from test_distribution import fixture


class RedirectResponse:
    def __init__(self, body: bytes, final_url: str):
        self.body = io.BytesIO(body)
        self.final_url = final_url
        self.headers = {"Content-Length": str(len(body))}

    def geturl(self):
        return self.final_url

    def read(self, size=-1):
        return self.body.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class MaterializationRedirectSecurityTests(unittest.TestCase):
    def test_unapproved_redirect_host_fails_closed_before_bytes_are_written(self):
        catalog, profile, payload = fixture()
        lock = resolve_distribution(catalog, profile)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FactoryError) as raised:
                materialize_artifacts(
                    lock,
                    tmp,
                    component_ids=["runtime"],
                    opener=lambda request, timeout: RedirectResponse(
                        payload,
                        "https://unapproved.example/runtime.bin",
                    ),
                )

            self.assertEqual(raised.exception.code, "materialize_redirect_host")
            self.assertFalse((Path(tmp) / "runtime.bin").exists())
            self.assertFalse(any(Path(tmp).glob("*.partial")))

    def test_approved_https_redirect_is_recorded_in_receipt(self):
        catalog, profile, payload = fixture()
        catalog["policy_defaults"]["allowed_source_hosts"].append("cdn.example.com")
        lock = resolve_distribution(catalog, profile)

        with tempfile.TemporaryDirectory() as tmp:
            result = materialize_artifacts(
                lock,
                tmp,
                component_ids=["runtime"],
                opener=lambda request, timeout: RedirectResponse(
                    payload,
                    "https://cdn.example.com/releases/runtime.bin",
                ),
            )

            receipt = result["artifacts"][0]
            self.assertEqual(receipt["origin_host"], "example.com")
            self.assertEqual(receipt["final_host"], "cdn.example.com")
            self.assertEqual(receipt["status"], "DOWNLOADED_VERIFIED")
            self.assertEqual((Path(tmp) / "runtime.bin").read_bytes(), payload)

    def test_redirect_scheme_downgrade_is_rejected(self):
        catalog, profile, payload = fixture()
        lock = resolve_distribution(catalog, profile)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FactoryError) as raised:
                materialize_artifacts(
                    lock,
                    tmp,
                    component_ids=["runtime"],
                    opener=lambda request, timeout: RedirectResponse(
                        payload,
                        "http://example.com/runtime.bin",
                    ),
                )

            self.assertEqual(raised.exception.code, "materialize_redirect_scheme")
            self.assertFalse((Path(tmp) / "runtime.bin").exists())


if __name__ == "__main__":
    unittest.main()
