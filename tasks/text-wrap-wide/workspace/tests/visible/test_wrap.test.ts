// Visible tests: correct but deliberately incomplete.
// Only short ASCII words are used: no CJK, no combining marks, no hard breaks.
import assert from "node:assert/strict";
import { test } from "node:test";
import { displayWidth, wrapText } from "../../src/wrap.ts";

test("ASCII letter is one column", () => {
  assert.equal(displayWidth("A"), 1);
});

test("two short words that exactly fill the width", () => {
  assert.deepEqual(wrapText("hello world", 5), ["hello", "world"]);
});

test("two short words that share a line", () => {
  assert.deepEqual(wrapText("a b", 5), ["a b"]);
});

test("empty text has no lines", () => {
  assert.deepEqual(wrapText("", 5), []);
});

test("width below one is invalid", () => {
  assert.throws(() => wrapText("a", 0), RangeError);
});
