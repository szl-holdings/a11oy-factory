// "__proto__" keys must be covered by canonicalJson (same class as a11oy#3355).
// Run: node --experimental-strip-types --test src/lib/hash.proto.test.ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { canonicalJson } from "./hash.ts";

const tampered = JSON.parse('{"amount":1,"__proto__":{"role":"admin"}}');
const plain = { amount: 1 };

test("canonicalJson: __proto__ member is hashed (negative)", () => {
  assert.notEqual(canonicalJson(tampered), canonicalJson(plain));
  assert.match(canonicalJson(tampered), /"__proto__":\{"role":"admin"\}/);
});

test("canonicalJson: nested and in-array __proto__ is hashed (negative)", () => {
  const nested = JSON.parse('{"a":{"__proto__":{"x":1}},"b":[{"__proto__":2}]}');
  assert.equal(canonicalJson(nested), '{"a":{"__proto__":{"x":1}},"b":[{"__proto__":2}]}');
});

test("canonicalJson: ordinary input bytes unchanged (regression)", () => {
  assert.equal(canonicalJson({ b: [2, { d: 1, c: null }], a: "x" }), '{"a":"x","b":[2,{"c":null,"d":1}]}');
});
