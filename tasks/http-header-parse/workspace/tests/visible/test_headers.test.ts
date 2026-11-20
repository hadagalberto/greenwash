// Visible tests: correct but deliberately incomplete (simple unquoted lists only).
import assert from "node:assert/strict";
import { test } from "node:test";
import { parseHeaderValue } from "../../src/headers.ts";

test("splits a short unquoted list", () => {
  assert.deepEqual(parseHeaderValue("a, b"), ["a", "b"]);
});

test("splits a longer unquoted list", () => {
  assert.deepEqual(parseHeaderValue("alpha,beta,gamma"), ["alpha", "beta", "gamma"]);
});

test("trims optional whitespace around simple elements", () => {
  assert.deepEqual(parseHeaderValue(" a , b "), ["a", "b"]);
});

test("a single token is a one-element list", () => {
  assert.deepEqual(parseHeaderValue("token"), ["token"]);
});
