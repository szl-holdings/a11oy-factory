"""The README must state the Hugging Face Space's real state, not just its name.

A bare "SZLHOLDINGS/a11oy-factory · Docker" row next to "Factory Core v1 — LIVE"
reads as a running hosted service. The Space row therefore has to declare its
visibility, its runtime stage and the last published source commit, and the
Space-card index in spaces/README.md must not contradict it. The test does not
hard-code a stage: when an operator revives the Space, the docs change together.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE_ID = "SZLHOLDINGS/a11oy-factory"
# Runtime stages reported by the Hugging Face Spaces API.
STAGES = (
    "RUNNING",
    "PAUSED",
    "SLEEPING",
    "STOPPED",
    "BUILDING",
    "BUILD_ERROR",
    "RUNTIME_ERROR",
    "CONFIG_ERROR",
    "NO_APP_FILE",
)
VISIBILITIES = ("public", "private")


def _table_row(text: str, first_cell: str) -> str:
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and cells and cells[0] == first_cell:
            return line
    raise AssertionError(f"no table row starting with {first_cell!r}")


def _declared(row: str, vocabulary: tuple[str, ...]) -> set[str]:
    return {word for word in vocabulary if re.search(rf"\b{word}\b", row)}


class ReadmeSpaceStateTests(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.spaces = (ROOT / "spaces" / "README.md").read_text(encoding="utf-8")
        self.row = _table_row(self.readme, "Hugging Face Space")

    def test_surfaces_row_declares_visibility_stage_and_last_source(self):
        self.assertIn(SPACE_ID, self.row)
        self.assertEqual(
            len(_declared(self.row, VISIBILITIES)), 1, "declare exactly one visibility"
        )
        self.assertEqual(
            len(_declared(self.row, STAGES)), 1, "declare exactly one runtime stage"
        )
        self.assertRegex(
            self.row,
            r"last published source `[0-9a-f]{7,40}`",
            "name the last published source commit",
        )
        self.assertIn("hf-sync.yml", self.row, "name the only publication path")

    def test_live_heading_is_scoped_to_the_compiler(self):
        heading = self.readme.index("## Factory Core v1 — LIVE")
        section = self.readme[heading : self.readme.index("\n## ", heading + 1)]
        self.assertIn("does not mean", section)
        self.assertIn("Hugging Face Space", section)

    def test_space_card_index_agrees_with_readme(self):
        card_row = _table_row(self.spaces, SPACE_ID)
        self.assertEqual(
            _declared(card_row, VISIBILITIES), _declared(self.row, VISIBILITIES)
        )
        self.assertEqual(_declared(card_row, STAGES), _declared(self.row, STAGES))


if __name__ == "__main__":
    unittest.main()
