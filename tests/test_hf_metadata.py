import unittest
from pathlib import Path


class HuggingFaceMetadataTests(unittest.TestCase):
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
