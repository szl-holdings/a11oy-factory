import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  LIST_ENDPOINT,
  ORG_CARD_ENDPOINT,
  SCHEMA,
  buildInventory,
  serialize,
} from "./generate-hf-space-inventory.mjs";

function fakeHub(routes) {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url, init });
    if (!(url in routes)) throw new Error(`unexpected URL ${url}`);
    const [status, body] = routes[url];
    return { status, ok: status >= 200 && status < 300, json: async () => body };
  };
  return { calls, fetchImpl };
}

const NOW = () => new Date("2026-09-29T12:34:56.789Z");

describe("generate-hf-space-inventory", () => {
  it("lists public Space ids sorted, adds the public org card, and never authenticates", async () => {
    const hub = fakeHub({
      [LIST_ENDPOINT]: [200, [{ id: "SZLHOLDINGS/zeta" }, { id: "SZLHOLDINGS/alpha", private: false }]],
      [ORG_CARD_ENDPOINT]: [200, { id: "SZLHOLDINGS/README", private: false }],
    });
    const inventory = await buildInventory({ fetchImpl: hub.fetchImpl, now: NOW });
    assert.equal(inventory.schema, SCHEMA);
    assert.equal(inventory.observed_at, "2026-09-29T12:34:56Z");
    assert.deepEqual(inventory.public_space_ids, [
      "SZLHOLDINGS/README",
      "SZLHOLDINGS/alpha",
      "SZLHOLDINGS/zeta",
    ]);
    for (const call of hub.calls) {
      assert.equal(call.init.redirect, "error");
      assert.equal(call.init.headers.Authorization, undefined);
    }
    assert.ok(serialize(inventory).endsWith("}\n"));
  });

  it("omits the org card when it is not publicly readable", async () => {
    const hub = fakeHub({
      [LIST_ENDPOINT]: [200, [{ id: "SZLHOLDINGS/alpha" }]],
      [ORG_CARD_ENDPOINT]: [401, null],
    });
    const inventory = await buildInventory({ fetchImpl: hub.fetchImpl, now: NOW });
    assert.deepEqual(inventory.public_space_ids, ["SZLHOLDINGS/alpha"]);
  });

  it("fails closed on provider errors and malformed rows", async () => {
    const cases = [
      [[500, null], /HTTP 500/],
      [[200, { id: "SZLHOLDINGS/alpha" }], /not a JSON array/],
      [[200, [{ id: "other/alpha" }]], /valid SZLHOLDINGS id/],
      [[200, [{ id: "SZLHOLDINGS/a" }, { id: "SZLHOLDINGS/a" }]], /duplicate/],
      [[200, [{ id: "SZLHOLDINGS/secret", private: true }]], /private Space/],
      [[200, Array.from({ length: 1000 }, (_, i) => ({ id: `SZLHOLDINGS/s${i}` }))], /paginate/],
    ];
    for (const [response, message] of cases) {
      const hub = fakeHub({ [LIST_ENDPOINT]: response, [ORG_CARD_ENDPOINT]: [200, null] });
      await assert.rejects(buildInventory({ fetchImpl: hub.fetchImpl, now: NOW }), message);
    }
  });
});
