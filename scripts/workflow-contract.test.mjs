import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { projectRoot } from "./with-app-env.mjs";

function workflow(name) {
  return readFileSync(join(projectRoot(), ".github", "workflows", name), "utf8");
}

function requireInOrder(source, markers) {
  let cursor = -1;
  for (const marker of markers) {
    const next = source.indexOf(marker, cursor + 1);
    assert.notEqual(next, -1, `workflow is missing ${JSON.stringify(marker)}`);
    assert.ok(next > cursor, `${JSON.stringify(marker)} is out of order`);
    cursor = next;
  }
}

test("CI fails closed and exercises tests, live auth, and typecheck", () => {
  const ci = workflow("ci.yml");

  assert.match(ci, /^  pull_request:\s*$/m);
  assert.match(ci, /^\s*run: npm ci\s*$/m);
  assert.doesNotMatch(ci, /npm install/);
  assert.doesNotMatch(ci, /if\s+npm ci|npm ci\s*\|\||continue-on-error/);

  requireInOrder(ci, [
    "run: npm ci",
    "run: npm test",
    "npm run dev",
    "http://127.0.0.1:8080/__app-env",
    "npm run check:auth",
    "run: npm run typecheck",
    "run: npm run build",
  ]);
  assert.match(ci, /trap cleanup EXIT/);
  assert.match(ci, /VITE_AUTH_ENABLED: "true"/);
});

test("Hugging Face publication is manual, source-bound, and environment-gated", () => {
  const sync = workflow("hf-sync.yml");

  assert.match(sync, /^  workflow_dispatch:\s*$/m);
  assert.doesNotMatch(sync, /^  push:\s*$/m);
  assert.match(sync, /^      source_sha:\s*$/m);
  assert.match(sync, /name: hugging-face-production/);
  assert.match(sync, /secrets\.HF_FACTORY_PRODUCTION_TOKEN/);
  assert.doesNotMatch(sync, /secrets\.HF_ORG_TOKEN|secrets\.HF_TOKEN/);
  assert.match(sync, /cancel-in-progress: false/);
  // D3: one lock per Hub asset, never keyed by event.
  assert.match(sync, /^concurrency:\n  group: hf-write\/space\/SZLHOLDINGS\/a11oy-factory\n  cancel-in-progress: false$/m);
  assert.match(sync, /FACTORY_SOURCE_SHA: \$\{\{ inputs\.source_sha \}\}/);
  assert.match(sync, /ref: \$\{\{ inputs\.source_sha \}\}/);
  assert.match(sync, /\^\[0-9a-f\]\{40\}\$/);
  assert.match(
    sync,
    /- name: Upload deployment proof\s+if: always\(\)/,
  );

  requireInOrder(sync, [
    "Validate requested source SHA shape",
    "ref: ${{ inputs.source_sha }}",
    "Prove exact source is current main",
    "git rev-parse HEAD",
    "refs/remotes/origin/main",
    "Acquire Space publisher credential (Trusted Publisher first)",
    "Publish factory Space",
    "Prove deployed runtime and public API contract",
    "Remove the ephemeral publisher credential",
  ]);
});

test("Hugging Face credential is Trusted Publisher first with one environment-scoped fallback", () => {
  const sync = workflow("hf-sync.yml");
  const job = sync.split("    steps:", 1)[0];

  assert.match(sync, /^  id-token: write$/m);
  assert.doesNotMatch(job, /HF_TOKEN/, "no token in the job-wide environment");
  assert.match(sync, /repository: szl-holdings\/\.github\n\s+ref: [0-9a-f]{40}\n/);
  assert.match(sync, /--target-repo SZLHOLDINGS\/a11oy-factory/);
  assert.match(sync, /--oidc-resource spaces\/SZLHOLDINGS\/a11oy-factory/);
  assert.doesNotMatch(sync, /--allow-create/);
  // Exactly one secret reference, and only in the selector's fallback slot.
  assert.equal(sync.match(/secrets\./g)?.length, 1);
  assert.match(sync, /^          HF_TOKEN_CANDIDATE: \$\{\{ secrets\.HF_FACTORY_PRODUCTION_TOKEN \}\}$/m);
  // The selector checkout must not survive into the publisher's clean-tree check.
  requireInOrder(sync, ["rm -rf .shared-github", "python \"$selector\"", "Publish factory Space"]);
  assert.match(sync, /- name: Remove the ephemeral publisher credential\n\s+if: always\(\)/);
  assert.match(sync, /\$\{\{ runner\.temp \}\}\/hf-publisher-credential\.json/);
});

test("Hugging Face client is the single org-pinned version (D6)", () => {
  const sync = workflow("hf-sync.yml");

  // One exact install of the org pin; no second, looser or older hub spec.
  const specs = sync.match(/huggingface[_-]hub[^"\s]*/g) ?? [];
  assert.deepEqual(specs, ["huggingface_hub==2.0.0"]);
  requireInOrder(sync, [
    "Install pinned Hugging Face client",
    '"huggingface_hub==2.0.0"',
    "Acquire Space publisher credential (Trusted Publisher first)",
  ]);
});

test("publisher has defense-in-depth source checks and runtime provenance", () => {
  const publisher = readFileSync(
    join(projectRoot(), ".github", "scripts", "publish_factory_space.py"),
    "utf8",
  );

  assert.match(publisher, /FACTORY_SOURCE_SHA/);
  assert.match(publisher, /prove_source_binding/);
  assert.match(publisher, /git\(root, "rev-parse", "HEAD"\)/);
  assert.match(publisher, /git\(root, "ls-remote"/);
  assert.match(publisher, /parent_commit=provider_sha/);
  assert.match(publisher, /delete_patterns="\*"/);
  assert.match(publisher, /commit_message=f"[^"\n]*\{source_sha\}"/);
  assert.match(publisher, /Hub mutation blocked\./);
});
