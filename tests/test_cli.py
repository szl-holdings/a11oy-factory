"""CLI contract: `act --payload` fails closed on input it cannot receipt."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, "-m", "a11oy_factory", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode, json.loads(result.stdout)


class ActPayloadTests(unittest.TestCase):
    def test_object_payload_is_receipted(self):
        code, rec = run_cli("act", "--cell", "lyte", "--payload", '{"signal": "bind"}')
        self.assertEqual(code, 0)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["decision"], "ALLOW")
        self.assertEqual(len(rec["payload_digest"]), 64)

    def test_malformed_json_payload_fails_closed(self):
        code, rec = run_cli("act", "--cell", "lyte", "--payload", "{not json")
        self.assertEqual(code, 2)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["decision"], "BLOCKED")
        self.assertEqual(rec["error"]["code"], "invalid_json")
        self.assertNotIn("payload_digest", rec)

    def test_non_object_payload_fails_closed(self):
        for raw in ("[1, 2]", '"text"', "7", "null"):
            with self.subTest(payload=raw):
                code, rec = run_cli("act", "--cell", "lyte", "--payload", raw)
                self.assertEqual(code, 2)
                self.assertEqual(rec["decision"], "BLOCKED")
                self.assertEqual(rec["error"]["code"], "invalid_payload")
                self.assertNotIn("payload_digest", rec)

    def test_frontier_act_still_exits_nonzero(self):
        code, rec = run_cli("act", "--cell", "N22", "--payload", '{"agent": "counsel"}')
        self.assertEqual(code, 2)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["decision"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
