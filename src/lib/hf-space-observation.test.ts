import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  inventorySummary,
  observeSpace,
  validateInventory,
} from "./hf-space-observation.ts";

const committed = JSON.parse(
  readFileSync(new URL("./data/hf-space-inventory.json", import.meta.url), "utf8"),
);
const spacesSource = readFileSync(new URL("./spaces.ts", import.meta.url), "utf8");

function inventory(ids: string[]) {
  return validateInventory({ ...committed, public_space_ids: ids });
}

describe("generated Hub Space inventory", () => {
  it("the committed file is exactly what the generator writes", () => {
    const valid = validateInventory(committed);
    assert.equal(valid.generator, "scripts/generate-hf-space-inventory.mjs");
    assert.ok(valid.public_space_ids.length > 0);
  });

  it("observes a listed Space and links it", () => {
    const observed = observeSpace(inventory(["SZLHOLDINGS/a11oy"]), "SZLHOLDINGS/a11oy");
    assert.equal(observed.state, "PUBLIC_OBSERVED");
    assert.equal(observed.url, "https://huggingface.co/spaces/SZLHOLDINGS/a11oy");
    assert.equal(observed.observed_at, committed.observed_at);
  });

  it("never links a Space the public read did not see", () => {
    const missing = observeSpace(inventory(["SZLHOLDINGS/a11oy"]), "SZLHOLDINGS/lyte-services");
    assert.equal(missing.state, "NOT_OBSERVED");
    assert.equal(missing.url, null);
    assert.match(missing.note, /private, or not on the Hub/);
  });

  it("counts come from the inventory, not from a typed number", () => {
    const summary = inventorySummary(inventory(["SZLHOLDINGS/a", "SZLHOLDINGS/b"]));
    assert.equal(summary.public_spaces_observed, 2);
    assert.equal(summary.observed_at, committed.observed_at);
    assert.doesNotMatch(spacesSource, /live_org_page_2026_08_29/);
    assert.doesNotMatch(spacesSource, /live org page now lists/i);
  });

  it("fails closed on a malformed inventory", () => {
    const bad = [
      null,
      { ...committed, schema: "other/v1" },
      { ...committed, observation_mode: "AUTHENTICATED" },
      { ...committed, observed_at: "2026-09-29" },
      { ...committed, generator: "hand-typed" },
      { ...committed, public_space_ids: [] },
      { ...committed, public_space_ids: ["other-org/space"] },
      { ...committed, public_space_ids: ["SZLHOLDINGS/b", "SZLHOLDINGS/a"] },
      { ...committed, public_space_ids: ["SZLHOLDINGS/a", "SZLHOLDINGS/a"] },
    ];
    for (const value of bad) assert.throws(() => validateInventory(value), /hf-space-inventory:/);
  });
});
