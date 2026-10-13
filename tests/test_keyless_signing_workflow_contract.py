# Copyright 2026 SZL Holdings — SPDX-License-Identifier: Apache-2.0
"""Regression tests for the assurance-to-signing artifact contract."""

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from a11oy_factory.assurance import AssuranceError
from a11oy_factory.distribution_resolver import resolve_distribution


ROOT = Path(__file__).resolve().parents[1]
SIGNING_WORKFLOW = ROOT / ".github" / "workflows" / "factory-keyless-signing.yml"
ASSURANCE_WORKFLOW = ROOT / ".github" / "workflows" / "factory-supply-chain-assurance.yml"
SUBJECT_BUILDER_PATH = ROOT / "scripts" / "build_assurance_signing_subject.py"
SUBJECT_BUILDER_SPEC = importlib.util.spec_from_file_location(
    "a11oy_factory_test_subject_builder",
    SUBJECT_BUILDER_PATH,
)
assert SUBJECT_BUILDER_SPEC and SUBJECT_BUILDER_SPEC.loader
SUBJECT_BUILDER = importlib.util.module_from_spec(SUBJECT_BUILDER_SPEC)
sys.modules[SUBJECT_BUILDER_SPEC.name] = SUBJECT_BUILDER
SUBJECT_BUILDER_SPEC.loader.exec_module(SUBJECT_BUILDER)


class KeylessSigningWorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signing = SIGNING_WORKFLOW.read_text(encoding="utf-8")
        self.assurance = ASSURANCE_WORKFLOW.read_text(encoding="utf-8")
        self.subject_builder = SUBJECT_BUILDER_PATH.read_text(encoding="utf-8")

    @staticmethod
    def _resolved_lock() -> dict:
        catalog = json.loads((ROOT / "factory" / "catalog.json").read_text(encoding="utf-8"))
        profile = json.loads(
            (ROOT / "factory" / "profiles" / "vllm-cpu-amd64.json").read_text(
                encoding="utf-8"
            )
        )
        return resolve_distribution(catalog, profile)

    def test_runtime_evidence_filename_matches_producer(self) -> None:
        self.assertIn(
            "dist/assurance/runtime/runtime-execution.json",
            self.assurance,
        )
        self.assertIn(
            'RUNTIME_PROOF="$(find dist/signing/source -type f -name runtime-execution.json -print -quit)"',
            self.signing,
        )
        self.assertNotIn("runtime-proof.json", self.signing)

    def test_quoted_heredoc_reads_environment_not_literal_shell_syntax(self) -> None:
        self.assertIn("import os", self.signing)
        self.assertIn(
            'Path(os.environ["INITIAL_STABLE_VERDICT"])',
            self.signing,
        )
        self.assertNotIn('Path("${INITIAL_STABLE_VERDICT}")', self.signing)

    def test_direct_script_invocations_can_import_repository_package(self) -> None:
        self.assertIn("PYTHONPATH: ${{ github.workspace }}", self.signing)

    def test_assurance_requires_runtime_run_exact_source_revision(self) -> None:
        self.assertIn('EXPECTED_SOURCE_SHA: ${{ github.sha }}', self.assurance)
        self.assertIn('test "$RUNTIME_SOURCE_SHA" = "$EXPECTED_SOURCE_SHA"', self.assurance)
        self.assertIn('--source-sha "$EXPECTED_SOURCE_SHA"', self.assurance)
        self.assertIn('--run-id "$GITHUB_RUN_ID"', self.assurance)
        self.assertIn('--run-attempt "$GITHUB_RUN_ATTEMPT"', self.assurance)
        self.assertIn('artifact-ids: ${{ needs.runtime.outputs.artifact_id }}', self.assurance)
        self.assertIn("runtime-workflow-head-sha.txt", self.assurance)
        self.assertNotIn("vllm-cpu-runtime-execution.yml/runs", self.assurance)

    def test_signing_requires_assurance_run_exact_source_revision(self) -> None:
        self.assertIn(
            'TRIGGER_HEAD_SHA: ${{ github.event.workflow_run.head_sha }}',
            self.signing,
        )
        self.assertIn('.head_sha == $source', self.signing)
        self.assertIn('test "$RUN_HEAD_SHA" = "$SOURCE_SHA"', self.signing)
        self.assertIn('ref: ${{ steps.resolve.outputs.source_sha }}', self.signing)
        self.assertIn('--source-sha "$SOURCE_SHA"', self.signing)
        self.assertIn("assurance-run-head-sha.txt", self.signing)

    def test_signing_crosschecks_runtime_producer_revision(self) -> None:
        self.assertIn("runtime-workflow-head-sha.txt", self.signing)
        self.assertIn('= "$SOURCE_SHA"', self.signing)

    def test_signing_subject_source_revision_is_explicit_and_exact(self) -> None:
        revision = "a" * 40
        self.assertEqual(SUBJECT_BUILDER._source_revision(revision), revision)
        for invalid in ("", "a" * 39, "A" * 40, "g" * 40):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AssuranceError) as raised:
                    SUBJECT_BUILDER._source_revision(invalid)
                self.assertEqual(raised.exception.code, "INVALID_SOURCE_REVISION")
        self.assertNotIn('os.environ.get("GITHUB_SHA"', self.subject_builder)

    def test_signing_subject_consumes_resolver_lock_digest(self) -> None:
        lock = self._resolved_lock()
        self.assertEqual(
            SUBJECT_BUILDER._distribution_lock_identity(lock),
            lock["lock_digest"],
        )

    def test_signing_subject_rejects_tampered_lock_digest(self) -> None:
        lock = self._resolved_lock()
        lock["lock_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_DIGEST_MISMATCH")

    def test_signing_subject_rejects_legacy_id_fallback(self) -> None:
        lock = self._resolved_lock()
        lock["id"] = lock.pop("lock_digest")
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_DIGEST_MISSING")

    def test_signing_subject_rejects_receipt_binding_mismatch(self) -> None:
        lock = deepcopy(self._resolved_lock())
        lock["receipt"]["subject"]["digest"]["sha256"] = "0" * 64
        with self.assertRaises(AssuranceError) as raised:
            SUBJECT_BUILDER._distribution_lock_identity(lock)
        self.assertEqual(raised.exception.code, "LOCK_RECEIPT_BINDING_MISMATCH")

    def test_workflows_watch_this_contract_test(self) -> None:
        watched_path = '"tests/test_keyless_signing_workflow_contract.py"'
        self.assertGreaterEqual(self.signing.count(watched_path), 1)
        self.assertGreaterEqual(self.assurance.count(watched_path), 2)

    @staticmethod
    def _event_block(workflow: str, event: str) -> str:
        header = workflow.split("\npermissions:", 1)[0]
        match = re.search(rf"^  {event}:\n(.*?)(?=^  \w+:|\Z)", header, re.M | re.S)
        return match.group(1) if match else ""

    def test_signing_waits_for_assurance_completion_instead_of_racing_push(self) -> None:
        self.assertEqual(self._event_block(self.signing, "push"), "")
        upstream = self._event_block(self.signing, "workflow_run")
        self.assertIn("branches: [main]", upstream)
        self.assertIn('workflows: ["factory-supply-chain-assurance"]', upstream)
        self.assertIn("types: [completed]", upstream)
        self.assertIn("github.event.workflow_run.head_sha || github.sha", self.signing)
        self.assertIn("cancel-in-progress: false", self.signing)

    def test_every_signing_change_produces_exact_source_assurance(self) -> None:
        paths = re.findall(r'^      - "([^"]+)"$', self._event_block(self.signing, "pull_request"), re.M)
        self.assertTrue(paths)
        for event in ("push", "pull_request"):
            assurance_paths = re.findall(r'^      - "([^"]+)"$', self._event_block(self.assurance, event), re.M)
            self.assertFalse(set(paths) - set(assurance_paths), event)

    def _resolve_script(self) -> str:
        step = self.signing.split("      - name: Resolve exact-head successful assurance evidence run\n", 1)[1]
        step = step.split("\n      - name:", 1)[0]
        body = step.split("        run: |\n", 1)[1]
        return "\n".join(line[10:] for line in body.splitlines())

    def _run_resolution(self, run: dict, *, event: str = "workflow_run", ref: str = "refs/heads/main") -> subprocess.CompletedProcess:
        if not shutil.which("bash") or not shutil.which("jq"):
            self.skipTest("workflow replay requires bash and jq (present on its Ubuntu runner)")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "run.json"
            fixture.write_text(json.dumps(run), encoding="utf-8")
            gh = root / "gh"
            gh.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "with open(os.environ['TEST_RUN']) as f: run=json.load(f)\n"
                "print(json.dumps({'workflow_runs': [run]} if '/workflows/' in sys.argv[-1] else run))\n",
                encoding="utf-8",
            )
            gh.chmod(0o700)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                       TEST_RUN=str(fixture), EVENT_NAME=event, TRIGGER_RUN_ID="42",
                       TRIGGER_HEAD_SHA="a" * 40, GITHUB_SHA="a" * 40,
                       GITHUB_REF=ref, GITHUB_REPOSITORY="szl-holdings/a11oy-factory",
                       GITHUB_ENV=str(root / "env"), GITHUB_OUTPUT=str(root / "output"))
            return subprocess.run(["bash", "-c", self._resolve_script()], env=env,
                                  capture_output=True, text=True, timeout=10)

    @staticmethod
    def _successful_run() -> dict:
        return {"id": 42, "head_sha": "a" * 40, "head_branch": "main",
                "head_repository": {"full_name": "szl-holdings/a11oy-factory"},
                "conclusion": "success", "event": "push",
                "path": ".github/workflows/factory-supply-chain-assurance.yml"}

    def test_resolver_accepts_only_completed_exact_source_trusted_assurance(self) -> None:
        good = self._successful_run()
        for event in ("workflow_run", "workflow_dispatch"):
            result = self._run_resolution(good, event=event)
            self.assertEqual(result.returncode, 0, result.stderr)
        for change in ({"head_sha": "b" * 40}, {"head_branch": "feature"},
                       {"conclusion": None}, {"conclusion": "failure"},
                       {"event": "pull_request"}, {"path": ".github/workflows/other.yml"},
                       {"head_repository": {"full_name": "other/factory"}}):
            with self.subTest(change=change):
                self.assertNotEqual(self._run_resolution(dict(good, **change)).returncode, 0)
        self.assertNotEqual(self._run_resolution(good, event="push").returncode, 0)
        self.assertNotEqual(self._run_resolution(good, event="workflow_dispatch", ref="refs/heads/feature").returncode, 0)
        self.assertNotEqual(self._run_resolution(dict(good, head_sha="b" * 40), event="workflow_dispatch").returncode, 0)

    def test_gate_distinguishes_successful_signing_from_expected_refusal(self) -> None:
        if not shutil.which("bash"):
            self.skipTest("workflow replay requires bash")
        step = self.signing.split("      - name: Require contract and real signing execution\n", 1)[1]
        script = "\n".join(line[10:] for line in step.split("        run: |\n", 1)[1].splitlines())
        env = dict(os.environ, EVENT_NAME="workflow_run", WORKFLOW_RUN_CONCLUSION="success",
                   WORKFLOW_RUN_EVENT="push", WORKFLOW_RUN_BRANCH="main",
                   WORKFLOW_RUN_REPOSITORY="szl-holdings/a11oy-factory",
                   GITHUB_REPOSITORY="szl-holdings/a11oy-factory",
                   CONTRACT_RESULT="success", SIGN_RESULT="success")
        cases = [({}, True), ({"SIGN_RESULT": "skipped"}, False),
                 ({"CONTRACT_RESULT": "failure"}, False),
                 ({"EVENT_NAME": "pull_request", "SIGN_RESULT": "skipped"}, True),
                 ({"WORKFLOW_RUN_CONCLUSION": "failure", "SIGN_RESULT": "skipped"}, True),
                 ({"WORKFLOW_RUN_EVENT": "pull_request", "SIGN_RESULT": "skipped"}, True),
                 ({"WORKFLOW_RUN_REPOSITORY": "other/factory", "SIGN_RESULT": "skipped"}, True),
                 ({"WORKFLOW_RUN_EVENT": "pull_request"}, False),
                 ({"EVENT_NAME": "workflow_dispatch"}, True)]
        for change, expected in cases:
            with self.subTest(change=change):
                result = subprocess.run(["bash", "-c", script], env=dict(env, **change),
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode == 0, expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
