// Visible tests: correct but deliberately incomplete.
import assert from "node:assert/strict";
import { test } from "node:test";
import { decodeVarint, encodeVarint } from "../../src/varint.ts";

test("zero is a single zero byte", () => {
  assert.deepEqual(encodeVarint(0), [0]);
});

test("one is a single byte", () => {
  assert.deepEqual(encodeVarint(1), [1]);
});

test("decodes small single-byte values", () => {
  assert.equal(decodeVarint([0]), 0);
  assert.equal(decodeVarint([1]), 1);
  assert.equal(decodeVarint([4]), 4);
});
