import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { useMountSnapshot } from "./use-mount-snapshot.ts";

test("server rendering never reads a browser-backed snapshot", () => {
  let reads = 0;
  const read = () => { reads++; throw new Error("browser storage unavailable on server"); };
  function Probe() {
    const snapshot = useMountSnapshot(read);
    return createElement("span", null, snapshot ?? "pending");
  }
  assert.equal(renderToString(createElement(Probe)), "<span>pending</span>");
  assert.equal(reads, 0);
});
