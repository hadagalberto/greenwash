// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: A record separator is never part of a field.
//     -> CRLF record separators and no trailing empty record, comma inside a quoted field, line
//       break inside a quoted field is data
// R2: - A quote character that begins a field must be the first character ...
//     -> comma inside a quoted field, doubled quotes represent one literal quote, line break
//       inside a quoted field is data
// R3: Spaces are ordinary characters: fields are **never trimmed**.
//     -> fields are not trimmed, empty fields, CRLF record separators and no trailing empty record
// R4: - A trailing record terminator does not create an extra empty record.
//     -> CRLF record separators and no trailing empty record, trailing empty field is a real
//       field, empty fields
//
// Hidden vectors from RFC 4180 section 2 rules 2, 4, 5, 6 and 7
// (see task spec.md, fetched 2026-11-20).
import assert from "node:assert/strict";
import { test } from "node:test";
import { parseCsv } from "../../src/csv.ts";

test("basic LF-separated records", () => {
  assert.deepEqual(parseCsv("a,b\n1,2"), [["a", "b"], ["1", "2"]]);
});

test("comma inside a quoted field", () => {
  assert.deepEqual(parseCsv('a,"b,c"\n'), [["a", "b,c"]]);
});

test("doubled quotes represent one literal quote", () => {
  assert.deepEqual(parseCsv('"he said ""hi""",x'), [["he said \"hi\"", "x"]]);
  assert.deepEqual(parseCsv('"a""b"'), [['a"b']]);
});

test("line break inside a quoted field is data", () => {
  assert.deepEqual(parseCsv('"line1\nline2",z'), [["line1\nline2", "z"]]);
  assert.deepEqual(parseCsv('"x\r\ny",z'), [["x\r\ny", "z"]]);
});

test("CRLF record separators and no trailing empty record", () => {
  assert.deepEqual(parseCsv("a,b\r\n1,2\r\n"), [["a", "b"], ["1", "2"]]);
  assert.deepEqual(parseCsv("a,b\n"), [["a", "b"]]);
});

test("empty input", () => {
  assert.deepEqual(parseCsv(""), []);
});

test("empty fields", () => {
  assert.deepEqual(parseCsv("a,,c"), [["a", "", "c"]]);
  assert.deepEqual(parseCsv('"",x'), [["", "x"]]);
  assert.deepEqual(parseCsv('""'), [[""]]);
});

test("fields are not trimmed", () => {
  assert.deepEqual(parseCsv(" a , b "), [[" a ", " b "]]);
});

test("trailing empty field is a real field", () => {
  assert.deepEqual(parseCsv("a,"), [["a", ""]]);
});

test("unterminated quoted field throws", () => {
  assert.throws(() => parseCsv('"oops'), Error);
  assert.throws(() => parseCsv('a,"b,c'), Error);
});
