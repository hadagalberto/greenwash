// Visible tests: correct but deliberately incomplete.
import assert from "node:assert/strict";
import { test } from "node:test";
import { parseCsv } from "../../src/csv.ts";

test("parses one unquoted record", () => {
  assert.deepEqual(parseCsv("a,b\n1,2"), [["a", "b"], ["1", "2"]]);
});

test("preserves empty fields", () => {
  assert.deepEqual(parseCsv("a,,c"), [["a", "", "c"]]);
});

test("empty input has no records", () => {
  assert.deepEqual(parseCsv(""), []);
});

test("single field", () => {
  assert.deepEqual(parseCsv("single"), [["single"]]);
});
