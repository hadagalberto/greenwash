// Visible tests: correct but deliberately incomplete — simple safe relative paths only.
import assert from "node:assert/strict";
import { test } from "node:test";
import { safeJoin } from "../../src/path.ts";

test("joins a simple file name", () => {
  assert.equal(safeJoin("/srv/data", "file.txt"), "/srv/data/file.txt");
});

test("joins a relative subdirectory path", () => {
  assert.equal(safeJoin("/srv/data", "a/b.txt"), "/srv/data/a/b.txt");
});

test("joins another single segment", () => {
  assert.equal(safeJoin("/srv/data", "x"), "/srv/data/x");
});
