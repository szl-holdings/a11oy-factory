import re
import unittest
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"
SPACE_RUNTIME_STATES = ("RUNNING", "PAUSED", "SLEEPING", "STOPPED", "BUILDING", "RUNTIME_ERROR")


class HuggingFaceMetadataTests(unittest.TestCase):
    def test_space_surface_row_states_runtime_and_published_source(self):
        """The Surfaces row must not list the Space without its observed state.

        Merging main does not publish the Space, so the README has to say what
        the Space is actually serving: visibility, runtime stage, and the last
        GitHub source SHA that was published to it.
        """
        rows = [
            line
            for line in README.read_text(encoding="utf-8").splitlines()
            if line.startswith("| Hugging Face Space |")
        ]
        self.assertEqual(len(rows), 1, "expected exactly one Hugging Face Space surface row")
        row = rows[0]
        self.assertIn("`SZLHOLDINGS/a11oy-factory`", row)
        self.assertRegex(row, r"\b(private|public)\b", "row must state Space visibility")
        self.assertTrue(
            any(re.search(rf"\b{state}\b", row) for state in SPACE_RUNTIME_STATES),
            f"row must state an observed Space runtime stage: {row!r}",
        )
        self.assertRegex(
            row,
            r"last published source `[0-9a-f]{8,40}`",
            "row must name the last GitHub source SHA published to the Space",
        )
        self.assertIn("hf-sync.yml", row, "row must name the only publication path")

    def test_core_live_heading_is_scoped_to_the_compiler(self):
        text = README.read_text(encoding="utf-8")
        section = text.split("## Factory Core v1 — LIVE", 1)[1].split("\n## ", 1)[0]
        self.assertIn("not a hosted", section)


    def test_space_frontmatter_is_publishable(self):
        readme = Path(__file__).resolve().parents[1] / "README.md"
        lines = readme.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(lines), 3)
        self.assertEqual(lines[0], "---")
        try:
            end = lines.index("---", 1)
        except ValueError as exc:
            self.fail(f"README.md frontmatter is not closed: {exc}")

        metadata = {}
        for line in lines[1:end]:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            self.assertIn(":", line, f"Invalid frontmatter line: {line!r}")
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")

        self.assertEqual(metadata.get("title"), "A11oy Factory")
        self.assertEqual(metadata.get("sdk"), "docker")
        self.assertEqual(metadata.get("app_port"), "7860")
        description = metadata.get("short_description", "")
        self.assertTrue(description, "short_description is required")
        self.assertLessEqual(
            len(description),
            60,
            "Hugging Face requires short_description to be at most 60 characters",
        )


if __name__ == "__main__":
    unittest.main()
