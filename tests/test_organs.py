import unittest

from a11oy_factory.cells import FRONTIERS
from a11oy_factory.compiler import BLOCKED
from a11oy_factory.organs import act, roadmap


class OrganTests(unittest.TestCase):
    def test_roadmap_starts_every_frontier_and_admits_only_lyte(self):
        rm = roadmap()
        self.assertEqual(rm["phase"], "STARTED")
        self.assertEqual(rm["admitted"], ["lyte"])
        self.assertEqual(rm["live"], [])
        self.assertIsNone(rm["energy"])
        self.assertEqual(len(rm["started"]), len(FRONTIERS))
        self.assertEqual(len(rm["organs"]), len(FRONTIERS))
        self.assertTrue(all(o["phase"] == "STARTED" and not o["admitted"] and not o["live"] for o in rm["organs"]))

    def test_lyte_act_is_bind_only(self):
        rec = act("lyte", {"signal": "bind"})
        self.assertTrue(rec["ok"])
        self.assertFalse(rec["halt"])
        self.assertEqual(rec["phase"], "ADMITTED")
        self.assertFalse(rec["live"])
        self.assertIn("Bind only", rec["reason"])
        self.assertEqual(len(rec["hash"]), 64)

    def test_every_frontier_act_halts_and_stays_blocked(self):
        for cell in FRONTIERS:
            rec = act(cell.id, {})
            self.assertFalse(rec["ok"], cell.id)
            self.assertTrue(rec["halt"], cell.id)
            self.assertFalse(rec["live"], cell.id)
            self.assertEqual(rec["decision"], BLOCKED, cell.id)
            self.assertEqual(rec["phase"], "STARTED", cell.id)
            self.assertIsNone(rec["energy"])
            self.assertEqual(rec["signer"], "UNSIGNED-honest")
            if cell.id == "N13":
                self.assertEqual(rec["honesty"], "UNAVAILABLE")
                self.assertIsNone(rec.get("energy_j"))

    def test_serve_has_no_weights(self):
        rec = act("N1", {"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(rec["error"]["code"], "no_weights")
        self.assertEqual(rec["choices"], [])

    def test_schema_checks_types_but_is_not_live(self):
        rec = act("N12", {"schema": {"type": "object", "required": ["id"]}, "value": {"id": "x"}})
        self.assertTrue(rec["valid"])
        self.assertFalse(rec["ok"])
        self.assertTrue(rec["halt"])
        rec = act("N12", {"schema": {"type": "object", "required": ["id"]}, "value": {}})
        self.assertFalse(rec["valid"])

    def test_unknown_tool_fails_closed(self):
        rec = act("N14", {"method": "tools/call", "name": "shell.exec"})
        self.assertTrue(rec["halt"])
        self.assertIn("unknown tool", rec["reason"])
        listed = act("N14", {"method": "tools/list"})
        names = [t["name"] for t in listed["tools"]]
        self.assertEqual(names, ["receipt.write"])
        self.assertFalse(listed["ok"])

    def test_route_requires_key_and_known_provider(self):
        rec = act("N18", {"provider": "openai"})
        self.assertIn("Virtual key", rec["reason"])
        rec = act("N18", {"provider": "openai", "key": "sk-test"})
        self.assertIn("not admitted", rec["reason"])

    def test_identity_is_not_an_svid(self):
        rec = act("N22", {"agent": "counsel"})
        self.assertTrue(rec["spiffe_shaped"].startswith("spiffe://szl.holdings/agent/"))
        self.assertIsNone(rec["svid"])
        self.assertTrue(rec["halt"])

    def test_rails_halt_off_topic(self):
        rec = act("N23", {"topic": "wire money"})
        self.assertTrue(rec["halt"])
        self.assertIn("Off-rail", rec["reason"])

    def test_browser_does_not_navigate(self):
        rec = act("N24", {"url": "https://example.com"})
        self.assertFalse(rec["navigated"])

    def test_policy_denies_unknown_action(self):
        rec = act("N25", {"action": "shell.exec"})
        self.assertFalse(rec["allow"])

    def test_unknown_cell_fails_closed(self):
        rec = act("not-a-cell")
        self.assertTrue(rec["halt"])
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["honesty"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
