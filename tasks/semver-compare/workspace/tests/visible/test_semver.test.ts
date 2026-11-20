// Visible tests: correct but deliberately incomplete (no pre-releases here).
import assert from "node:assert/strict";
import { test } from "node:test";
import { compareSemver } from "../../src/semver.ts";

test("identical versions compare equal", () => {
  assert.equal(compareSemver("1.0.0", "1.0.0"), 0);
});

test("major version determines precedence", () => {
  assert.equal(compareSemver("1.0.0", "2.0.0"), -1);
});

test("minor version determines precedence", () => {
  assert.equal(compareSemver("2.1.0", "2.0.9"), 1);
});

test("multi-digit numeric components compare numerically", () => {
  assert.equal(compareSemver("1.10.0", "1.9.0"), 1);
});
