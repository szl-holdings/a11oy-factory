import assert from "node:assert/strict";
import test from "node:test";
import { refreshReceiptSelection, type ReceiptSelection } from "./receipt-selection.ts";

const a = { hash: "A", decision_id: "a" };
const b = { hash: "B", decision_id: "b" };
const entries = [a, b];
const empty = (): ReceiptSelection => ({ hash: undefined, entries: undefined, paste: "" });
const json = (value: unknown) => JSON.stringify(value, null, 2);

test("initial hydrated or client-only selection prefills a found receipt", () => {
  assert.equal(refreshReceiptSelection(empty(), "A", entries, a).paste, json(a));
});
test("A to B to missing to no hash to back retains JSON on misses and selects on return", () => {
  let state = refreshReceiptSelection(empty(), "A", entries, a);
  assert.equal(state.paste, json(a));
  state = refreshReceiptSelection(state, "B", entries, b);
  assert.equal(state.paste, json(b));
  state = refreshReceiptSelection(state, "missing", entries, null);
  assert.equal(state.paste, json(b));
  state = refreshReceiptSelection(state, undefined, entries, null);
  assert.equal(state.paste, json(b));
  state = refreshReceiptSelection(state, "A", entries, a);
  assert.equal(state.paste, json(a));
});
test("manual edits persist on rerender and misses, then a found selection replaces them", () => {
  const selected = refreshReceiptSelection(empty(), "A", entries, a);
  const edited = { ...selected, paste: "manually edited JSON" };
  assert.equal(refreshReceiptSelection(edited, "A", entries, a), edited);
  const missing = refreshReceiptSelection(edited, "missing", entries, null);
  assert.equal(missing.paste, edited.paste);
  assert.equal(refreshReceiptSelection(missing, "B", entries, b).paste, json(b));
});
test("clearing the selected ledger receipt retains the displayed JSON", () => {
  const selected = refreshReceiptSelection(empty(), "A", entries, a);
  const cleared = refreshReceiptSelection(selected, "A", [], null);
  assert.equal(cleared.paste, json(a));
});
test("a new ledger snapshot refreshes an existing selection exactly once", () => {
  const selected = refreshReceiptSelection(empty(), "A", entries, a);
  const edited = { ...selected, paste: "manual" };
  const refreshed = refreshReceiptSelection(edited, "A", [...entries], a);
  assert.equal(refreshed.paste, json(a));
  assert.equal(refreshReceiptSelection(refreshed, "A", refreshed.entries, a), refreshed);
});
