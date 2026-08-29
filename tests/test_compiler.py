import unittest

from a11oy_factory.cells import ADMITTED, FRONTIERS, LYTE
from a11oy_factory.compiler import BLOCKED, compile_cell


class CompilerTests(unittest.TestCase):
    def test_lyte_is_the_only_admitted_cell(self):
        self.assertEqual(ADMITTED, frozenset({"lyte"}))
        rec = compile_cell("lyte", signal="bind as a11oy package")
        self.assertEqual(rec.decision, "ALLOW")
        self.assertEqual(rec.bind, "BIND_AS_A11OY_PACKAGE")
        self.assertEqual(rec.flagship, "a11oy")
        self.assertEqual(rec.signer, "UNSIGNED-honest")
        self.assertIsNone(rec.energy)
        self.assertEqual(len(rec.hash), 64)

    def test_frontiers_are_blocked_roadmap(self):
        self.assertEqual(len(FRONTIERS), 8)
        for cell in FRONTIERS:
            rec = compile_cell(cell.id)
            self.assertEqual(rec.decision, BLOCKED)
            self.assertEqual(rec.honesty_tier, "ROADMAP")

    def test_unknown_fails_closed(self):
        rec = compile_cell("not-a-cell")
        self.assertEqual(rec.decision, BLOCKED)
        self.assertEqual(rec.honesty_tier, "UNAVAILABLE")

    def test_empty_fails_closed(self):
        rec = compile_cell("")
        self.assertEqual(rec.decision, BLOCKED)

    def test_lambda_never_proven(self):
        rec = compile_cell("lyte")
        self.assertEqual(rec.lambda_status, "Conjecture 1")


if __name__ == "__main__":
    unittest.main()
