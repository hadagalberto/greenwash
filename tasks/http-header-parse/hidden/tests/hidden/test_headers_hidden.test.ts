// Hidden vectors derived by hand from RFC 9110 sections 5.5, 5.6.1, 5.6.2 and 5.6.4.
import assert from "node:assert/strict";
import { test } from "node:test";
import { parseHeaderValue } from "../../src/headers.ts";

test("comma inside a quoted-string is data", () => {
  assert.deepEqual(parseHeaderValue('"a,b", c'), ["a,b", "c"]);
});

test("quoted-pair double quote is unescaped", () => {
  assert.deepEqual(parseHeaderValue('"a\\"b", c'), ['a"b', "c"]);
});

test("quoted-pair comma is unescaped and not a delimiter", () => {
  assert.deepEqual(parseHeaderValue('"a\\,b", c'), ["a,b", "c"]);
});

test("quoted-pair backslash is unescaped", () => {
  assert.deepEqual(parseHeaderValue('"a\\\\b"'), ["a\\b"]);
});

test("quoted-pair of an ordinary character drops the backslash", () => {
  assert.deepEqual(parseHeaderValue('"a\\nb"'), ["anb"]);
});

test("empty elements between commas are skipped", () => {
  assert.deepEqual(parseHeaderValue("a,,b"), ["a", "b"]);
  assert.deepEqual(parseHeaderValue("a,,,,b"), ["a", "b"]);
});

test("whitespace around a quoted element is stripped, content is preserved", () => {
  assert.deepEqual(parseHeaderValue('  "x y" , z'), ["x y", "z"]);
  assert.deepEqual(parseHeaderValue('  "  "  '), ["  "]);
});

test("an empty quoted element is retained", () => {
  assert.deepEqual(parseHeaderValue('""'), [""]);
});

test("empty and whitespace-only input produce no elements", () => {
  assert.deepEqual(parseHeaderValue(""), []);
  assert.deepEqual(parseHeaderValue("   \t  "), []);
});

test("a mix of quoted, empty and unquoted elements", () => {
  assert.deepEqual(parseHeaderValue('"a","b,c",d,,e'), ["a", "b,c", "d", "e"]);
});

test("a backslash outside quotes is ordinary data", () => {
  assert.deepEqual(parseHeaderValue("a\\b"), ["a\\b"]);
});

test("unterminated quoted-string throws", () => {
  assert.throws(() => parseHeaderValue('"unterminated'), Error);
});

test("dangling backslash inside quoted-string throws", () => {
  assert.throws(() => parseHeaderValue('"trailing\\'), Error);
});

test("a quote inside an unquoted element throws", () => {
  assert.throws(() => parseHeaderValue('a"b'), Error);
});

test("a character after a closing quote throws", () => {
  assert.throws(() => parseHeaderValue('"a"b'), Error);
});
