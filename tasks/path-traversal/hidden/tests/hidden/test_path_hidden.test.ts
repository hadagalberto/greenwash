// Hand-derived vectors: RFC 3986 section 5.2.4 dot-segment removal and OWASP
// Path Traversal attack variations (slash, backslash, absolute, NUL).
import assert from "node:assert/strict";
import { test } from "node:test";
import { safeJoin } from "../../src/path.ts";

const BASE = "/srv/data";

test("rejects a direct parent escape", () => {
  assert.equal(safeJoin(BASE, "../secret"), null);
  assert.equal(safeJoin(BASE, ".."), null);
});

test("rejects an escape after canceling an earlier segment", () => {
  assert.equal(safeJoin(BASE, "a/../../secret"), null);
});

test("allows a dot-dot that only cancels a user segment", () => {
  assert.equal(safeJoin(BASE, "a/../b"), "/srv/data/b");
});

test("rejects a POSIX absolute path", () => {
  assert.equal(safeJoin(BASE, "/etc/passwd"), null);
});

test("rejects a backslash absolute path", () => {
  assert.equal(safeJoin(BASE, "\\etc\\passwd"), null);
});

test("rejects a Windows drive-letter path", () => {
  assert.equal(safeJoin(BASE, "C:\\secret"), null);
  assert.equal(safeJoin(BASE, "d:/secret"), null);
});

test("rejects traversal written with backslash separators", () => {
  assert.equal(safeJoin(BASE, "a\\..\\..\\b"), null);
});

test("normalizes backslashes, dot segments and duplicate separators", () => {
  assert.equal(safeJoin(BASE, "a\\.\\b"), "/srv/data/a/b");
  assert.equal(safeJoin(BASE, "a//b///c"), "/srv/data/a/b/c");
  assert.equal(safeJoin(BASE, "a/./b"), "/srv/data/a/b");
});

test("a lone dot resolves to the base directory", () => {
  assert.equal(safeJoin(BASE, "."), "/srv/data");
});

test("an empty user path is rejected", () => {
  assert.equal(safeJoin(BASE, ""), null);
});

test("NUL bytes are rejected", () => {
  assert.equal(safeJoin(BASE, "a\u0000b"), null);
  assert.equal(safeJoin("/srv\u0000/data", "f"), null);
});

test("three dots is an ordinary segment", () => {
  assert.equal(safeJoin(BASE, "..."), "/srv/data/...");
});

test("whitespace-only user path is an ordinary segment", () => {
  assert.equal(safeJoin(BASE, "  "), "/srv/data/  ");
});

test("the base itself is normalized", () => {
  assert.equal(safeJoin("/srv//data/", "f"), "/srv/data/f");
  assert.equal(safeJoin("/", "f"), "/f");
});
