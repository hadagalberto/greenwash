// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: A comma inside a quoted-string is data, not a delimiter.
//     -> comma inside a quoted-string is data, dangling backslash inside quoted-string throws,
//       quoted-pair comma is unescaped and not a delimiter
// R2: Do **not** trim whitespace from the resulting content: spaces inside ...
//     -> a backslash outside quotes is ordinary data, comma inside a quoted-string is data,
//       whitespace around a quoted element is stripped, content is preserved
// R3: Skip empty unquoted elements: elements that contain only OWS after ...
//     -> empty and whitespace-only input produce no elements, a mix of quoted, empty and unquoted
//       elements, empty elements between commas are skipped
// R4: Throw an `Error` if a quoted-string is not terminated, if a quoted- ...
//     -> a character after a closing quote throws, dangling backslash inside quoted-string throws,
//       a quote inside an unquoted element throws
// R5: Outside a quoted-string a backslash is an ordinary data character ...
//     -> a backslash outside quotes is ordinary data, comma inside a quoted-string is data,
//       dangling backslash inside quoted-string throws
// R6: Return `[]` for empty input or input containing only OWS.
//     -> empty and whitespace-only input produce no elements, a mix of quoted, empty and unquoted
//       elements, an empty quoted element is retained
// R7: ## Sources (fetched 2026-11-20) - https://www.rfc- ...
//     -> empty and whitespace-only input produce no elements, whitespace around a quoted element
//       is stripped, content is preserved, a backslash outside quotes is ordinary data
// R8: - Section 5.6.2 "Tokens": double quote and comma are delimiters, so ...
//     -> comma inside a quoted-string is data, quoted-pair double quote is unescaped, dangling
//       backslash inside quoted-string throws
// R9: Recipients MUST handle a quoted-pair "as if it were replaced by the ...
//     -> quoted-pair backslash is unescaped, quoted-pair of an ordinary character drops the
//       backslash, dangling backslash inside quoted-string throws
//
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
