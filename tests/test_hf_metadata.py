import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
VERIFIER = ROOT / ".github" / "scripts" / "verify_factory_space.py"
SPACE_ROW_PREFIX = "| Hugging Face Space |"
SPACE_IDENTITY = "`SZLHOLDINGS/a11oy-factory`"
README_REPORTABLE_FAILURE_STAGES = ("BUILD_ERROR", "CONFIG_ERROR", "NO_APP_FILE", "DELETING")
# Every stage the verifier can observe (its terminal-failure and endpoint sets,
# plus BUILDING) is a truthful README report. Reporting is not a health claim.
SPACE_RUNTIME_STATES = (
    "RUNNING",
    "PAUSED",
    "SLEEPING",
    "STOPPED",
    "BUILDING",
    "RUNTIME_ERROR",
    *README_REPORTABLE_FAILURE_STAGES,
)
# The verifier waits through BUILDING: it is neither a terminal failure nor an
# endpoint stage, so it is the one reportable stage outside the verifier's sets.
VERIFIER_WAIT_STAGES = frozenset({"BUILDING"})


def space_surface_rows(text):
    return [line for line in text.splitlines() if line.startswith(SPACE_ROW_PREFIX)]


def space_row_problems(row):
    """Return every reason a Hugging Face Space surface row is not a complete status line.

    Accepting a stage here only lets the README report what the Hub observed;
    deployment health stays with .github/scripts/verify_factory_space.py.
    """
    problems = []
    if SPACE_IDENTITY not in row:
        problems.append(f"row must name the Space repository {SPACE_IDENTITY}")
    if not re.search(r"\b(private|public)\b", row):
        problems.append("row must state Space visibility")
    if not any(re.search(rf"\b{state}\b", row) for state in SPACE_RUNTIME_STATES):
        problems.append(f"row must state an observed Space runtime stage: {row!r}")
    if not re.search(r"last published source `[0-9a-f]{8,40}`", row):
        problems.append("row must name the last GitHub source SHA published to the Space")
    if "hf-sync.yml" not in row:
        problems.append("row must name the only publication path")
    return problems


def fixture_row(
    stage="PAUSED",
    *,
    identity=SPACE_IDENTITY,
    visibility="private",
    source="`ff484bf1`",
    workflow="`hf-sync.yml`",
):
    """A synthetic Space row shaped like the checked-in README row."""
    return (
        f"{SPACE_ROW_PREFIX} {identity} · Docker · {visibility} · {stage}, observed 2026-10-13"
        f" · last published source {source} (2026-09-08), behind `main`"
        f" · publishes only by operator dispatch of {workflow} |"
    )


def verifier_stage_sets():
    """Read the verifier's stage sets from its source without importing it.

    Importing verify_factory_space.py needs huggingface_hub, so parse the module
    and literal-evaluate only the two module-level stage-set assignments.
    """
    wanted = {"TERMINAL_FAILURE_STAGES", "ENDPOINT_STAGES"}
    found = {}
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"), filename=str(VERIFIER))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                if target.id in found:
                    raise AssertionError(f"verifier assigns {target.id} more than once")
                try:
                    found[target.id] = frozenset(ast.literal_eval(value))
                except ValueError as exc:
                    raise AssertionError(f"verifier {target.id} is no longer a literal set") from exc
    missing = sorted(wanted - found.keys())
    if missing:
        raise AssertionError(f"verifier no longer defines literal stage sets: {missing}")
    return found


def stage_contract_drift(contract, verifier_sets):
    """Compare a README stage contract with every stage the verifier classifies or waits through.

    "unreportable": the verifier can observe it but the README may not state it.
    "unclassified": the README would accept it but the verifier never classifies it.
    "duplicated": the contract lists it more than once.
    """
    observable = (
        verifier_sets["TERMINAL_FAILURE_STAGES"]
        | verifier_sets["ENDPOINT_STAGES"]
        | VERIFIER_WAIT_STAGES
    )
    accepted = set(contract)
    return {
        "unreportable": sorted(observable - accepted),
        "unclassified": sorted(accepted - observable),
        "duplicated": sorted(stage for stage in accepted if contract.count(stage) > 1),
    }


NO_STAGE_DRIFT = {"unreportable": [], "unclassified": [], "duplicated": []}


class HuggingFaceMetadataTests(unittest.TestCase):
    def test_space_surface_row_states_runtime_and_published_source(self):
        """The Surfaces row must not list the Space without its observed state.

        Merging main does not publish the Space, so the README has to say what
        the Space is actually serving: visibility, runtime stage, and the last
        GitHub source SHA that was published to it.
        """
        rows = space_surface_rows(README.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 1, "expected exactly one Hugging Face Space surface row")
        self.assertEqual(space_row_problems(rows[0]), [])

    def assert_fixture_accepts(self, stage):
        self.assertEqual(space_row_problems(fixture_row(stage)), [])

    def test_fixture_row_accepts_build_error(self):
        self.assert_fixture_accepts("BUILD_ERROR")

    def test_fixture_row_accepts_config_error(self):
        self.assert_fixture_accepts("CONFIG_ERROR")

    def test_fixture_row_accepts_no_app_file(self):
        self.assert_fixture_accepts("NO_APP_FILE")

    def test_fixture_row_accepts_deleting(self):
        self.assert_fixture_accepts("DELETING")

    def test_fixture_row_accepts_previously_supported_stages(self):
        for stage in ("RUNNING", "PAUSED", "SLEEPING", "STOPPED", "BUILDING", "RUNTIME_ERROR"):
            with self.subTest(stage=stage):
                self.assert_fixture_accepts(stage)

    def test_metadata_contract_accepts_every_verifier_observed_stage(self):
        sets = verifier_stage_sets()
        self.assertIn("RUNNING", sets["ENDPOINT_STAGES"])
        self.assertIn("RUNTIME_ERROR", sets["TERMINAL_FAILURE_STAGES"])
        observed = sets["TERMINAL_FAILURE_STAGES"] | sets["ENDPOINT_STAGES"] | VERIFIER_WAIT_STAGES
        self.assertEqual(sorted(observed - set(SPACE_RUNTIME_STATES)), [])
        for stage in sorted(observed):
            with self.subTest(stage=stage):
                self.assert_fixture_accepts(stage)

    def test_readme_stage_contract_equals_verifier_stage_sets(self):
        """The README contract and the verifier's sets must match in both directions.

        A stage the README could state but the verifier never classifies would
        let the README report a stage the deployment gate cannot judge.
        """
        sets = verifier_stage_sets()
        self.assertTrue(
            VERIFIER_WAIT_STAGES.isdisjoint(sets["TERMINAL_FAILURE_STAGES"] | sets["ENDPOINT_STAGES"]),
            "BUILDING is a wait stage; the verifier must not also classify it",
        )
        self.assertEqual(stage_contract_drift(SPACE_RUNTIME_STATES, sets), NO_STAGE_DRIFT)

    def test_stage_contract_drift_flags_extra_missing_and_duplicate_stages(self):
        sets = verifier_stage_sets()
        for label, contract, expected in (
            (
                "stage the verifier never classifies",
                (*SPACE_RUNTIME_STATES, "APP_STARTING"),
                {**NO_STAGE_DRIFT, "unclassified": ["APP_STARTING"]},
            ),
            (
                "verifier terminal stage dropped from the README contract",
                tuple(stage for stage in SPACE_RUNTIME_STATES if stage != "DELETING"),
                {**NO_STAGE_DRIFT, "unreportable": ["DELETING"]},
            ),
            (
                "wait stage dropped from the README contract",
                tuple(stage for stage in SPACE_RUNTIME_STATES if stage != "BUILDING"),
                {**NO_STAGE_DRIFT, "unreportable": ["BUILDING"]},
            ),
            (
                "stage listed twice",
                (*SPACE_RUNTIME_STATES, "PAUSED"),
                {**NO_STAGE_DRIFT, "duplicated": ["PAUSED"]},
            ),
        ):
            with self.subTest(case=label):
                self.assertEqual(stage_contract_drift(contract, sets), expected)

    def test_readme_reportable_failure_stages_remain_verifier_terminal_failures(self):
        sets = verifier_stage_sets()
        for stage in README_REPORTABLE_FAILURE_STAGES:
            with self.subTest(stage=stage):
                self.assertIn(stage, sets["TERMINAL_FAILURE_STAGES"])
                self.assertNotIn(stage, sets["ENDPOINT_STAGES"])

    def test_fixture_row_rejects_missing_unknown_or_malformed_stage(self):
        for label, stage in (
            ("no stage", ""),
            ("unknown stage", "HIBERNATING"),
            ("lowercase token", "paused"),
            ("hyphenated token", "BUILD-ERROR"),
            ("suffixed token", "RUNNINGX"),
            ("prefixed token", "XDELETING"),
            ("truncated token", "NO_APP"),
        ):
            with self.subTest(case=label):
                problems = space_row_problems(fixture_row(stage))
                self.assertEqual(len(problems), 1, problems)
                self.assertIn("observed Space runtime stage", problems[0])

    def test_fixture_row_rejects_missing_required_fields(self):
        for label, overrides, expected in (
            ("identity", {"identity": ""}, "Space repository"),
            ("visibility", {"visibility": ""}, "visibility"),
            ("published-source SHA", {"source": ""}, "source SHA"),
            ("hf-sync.yml", {"workflow": ""}, "publication path"),
        ):
            with self.subTest(missing=label):
                problems = space_row_problems(fixture_row("RUNNING", **overrides))
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(expected, problems[0])

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
