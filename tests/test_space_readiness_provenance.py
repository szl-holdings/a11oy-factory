"""Source-only, loopback-only regression for the factory readiness boundary."""

from __future__ import annotations

import importlib.util
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("a11oy_factory_space_readiness", ROOT / "space" / "server.py")
assert SPEC is not None and SPEC.loader is not None
space = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(space)


class SourceReadinessContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), space.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=5)

    def request(self, path: str, *, method: str = "GET") -> tuple[int, dict]:
        request = Request(self.origin + path, method=method)
        try:
            with urlopen(request, timeout=3) as response:
                status, raw = response.status, response.read()
        except HTTPError as exc:
            with exc:
                status, raw = exc.code, exc.read()
        return status, json.loads(raw) if raw else {}

    def test_unbound_source_refuses_get_and_head_readyz(self) -> None:
        for state in ("UNAVAILABLE", "INVALID"):
            with self.subTest(state=state), patch.object(
                space, "_source_provenance", return_value={"state": state}
            ), patch.object(space, "_catalog", return_value={}), patch.object(
                space, "_profile_summaries", return_value=[]
            ), patch.object(space, "catalog_summary", return_value={}):
                status, body = self.request("/readyz")
                self.assertEqual(status, 503)
                self.assertIs(body.get("ok"), False)
                self.assertEqual(body["source_provenance"]["state"], state)
                head_status, _ = self.request("/readyz", method="HEAD")
                self.assertEqual(head_status, 503)

    def test_bound_source_preserves_readyz_and_uncertified_runtime(self) -> None:
        with patch.object(space, "_source_provenance", return_value={
            "state": "BOUND", "github_repository": "szl-holdings/a11oy-factory",
            "github_source_sha": "a" * 40
        }), patch.object(space, "_catalog", return_value={}), patch.object(
            space, "_profile_summaries", return_value=[]
        ), patch.object(space, "catalog_summary", return_value={}):
            status, body = self.request("/readyz")
            self.assertEqual(status, 200)
            self.assertIs(body.get("ok"), True)
            self.assertIs(body["factory_core"]["runtime_certified"], False)
            head_status, _ = self.request("/readyz", method="HEAD")
            self.assertEqual(head_status, 200)

    def test_healthz_is_not_misrepresented_as_release_readiness(self) -> None:
        with patch.object(space, "_source_provenance", return_value={"state": "UNAVAILABLE"}), patch.object(
            space, "_catalog", return_value={}
        ), patch.object(space, "_profile_summaries", return_value=[]), patch.object(
            space, "catalog_summary", return_value={}
        ):
            status, body = self.request("/healthz")
            self.assertEqual(status, 200)
            self.assertIs(body.get("ok"), True)
            self.assertEqual(body["source_provenance"]["state"], "UNAVAILABLE")
            head_status, _ = self.request("/healthz", method="HEAD")
            self.assertEqual(head_status, 200)


if __name__ == "__main__":
    unittest.main()
