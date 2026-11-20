// Visible tests: correct but deliberately incomplete.
import assert from "node:assert/strict";
import { test } from "node:test";
import { satisfies } from "../../src/semver-range.ts";

test("caret accepts a compatible patch release", () => {
  assert.equal(satisfies("1.2.5", "^1.2.3"), true);
});

test("caret rejects the next major release", () => {
  assert.equal(satisfies("2.0.0", "^1.2.3"), false);
});

test("tilde accepts a patch release", () => {
  assert.equal(satisfies("1.2.9", "~1.2.3"), true);
});

test("space separated comparators are ANDed", () => {
  assert.equal(satisfies("1.5.0", ">=1.2.3 <2.0.0"), true);
});

test("exact version", () => {
  assert.equal(satisfies("1.2.3", "1.2.3"), true);
});

test("OR of two caret ranges", () => {
  assert.equal(satisfies("1.2.3", "^1.2.3 || ^2.0.0"), true);
});
