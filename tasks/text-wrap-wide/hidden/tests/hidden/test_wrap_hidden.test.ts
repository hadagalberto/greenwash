// Hidden vectors derived by hand from UAX #11 / UAX #29 and the task spec.
// https://www.unicode.org/reports/tr11/
// https://www.unicode.org/reports/tr29/
import assert from "node:assert/strict";
import { test } from "node:test";
import { displayWidth, wrapText } from "../../src/wrap.ts";

test("narrow and wide code points", () => {
  assert.equal(displayWidth("A"), 1);
  assert.equal(displayWidth("漢"), 2); // U+6F22 CJK UNIFIED IDEOGRAPH
  assert.equal(displayWidth("\uFF21"), 2); // fullwidth Latin A
  assert.equal(displayWidth("\u3042"), 2); // hiragana A
});

test("combining marks and ZWJ have zero advance width", () => {
  assert.equal(displayWidth("\u0301"), 0); // combining acute
  assert.equal(displayWidth("\u0308"), 0); // combining diaeresis
  assert.equal(displayWidth("\u20DD"), 0); // enclosing circle (Me)
  assert.equal(displayWidth("\u200D"), 0); // zero width joiner
  assert.equal(displayWidth("\uFE0F"), 0); // variation selector
});

test("greedy whole-word packing with a trailing word", () => {
  assert.deepEqual(wrapText("hello world", 5), ["hello", "world"]);
  assert.deepEqual(wrapText("a b c", 5), ["a b c"]);
  assert.deepEqual(wrapText("a b c", 3), ["a b", "c"]);
  assert.deepEqual(wrapText("a b", 3), ["a b"]);
});

test("space runs collapse and empty tokens vanish", () => {
  assert.deepEqual(wrapText("a  b", 3), ["a b"]);
  assert.deepEqual(wrapText("   ", 5), []);
  assert.deepEqual(wrapText("", 5), []);
});

test("wide characters and long ASCII words hard-break by columns", () => {
  assert.deepEqual(wrapText("漢字", 2), ["漢", "字"]);
  assert.deepEqual(wrapText("abc", 2), ["ab", "c"]);
});

test("combining marks remain with their base cluster", () => {
  assert.deepEqual(wrapText("e\u0301x", 1), ["e\u0301", "x"]);
  assert.deepEqual(wrapText("漢\u0301", 1), ["漢\u0301"]);
});

test("width below one throws RangeError", () => {
  assert.throws(() => wrapText("a", 0), RangeError);
  assert.throws(() => wrapText("a", -2), RangeError);
});

test("empty string and only first code point measured", () => {
  // spec.md: empty string has width 0; only the first code point is measured.
  assert.equal(displayWidth(""), 0);
  assert.equal(displayWidth("A漢"), 1);
});
