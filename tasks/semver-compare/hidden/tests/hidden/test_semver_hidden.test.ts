// Hidden vectors from the official SemVer 2.0.0 section 11 example chain.
// https://semver.org/spec/v2.0.0.html
import assert from "node:assert/strict";
import { test } from "node:test";
import { compareSemver } from "../../src/semver.ts";

test("alpha precedes alpha.1", () => {
  assert.equal(compareSemver("1.0.0-alpha", "1.0.0-alpha.1"), -1);
});

test("alpha.1 precedes alpha.beta", () => {
  assert.equal(compareSemver("1.0.0-alpha.1", "1.0.0-alpha.beta"), -1);
});

test("alpha.beta precedes beta", () => {
  assert.equal(compareSemver("1.0.0-alpha.beta", "1.0.0-beta"), -1);
});

test("numeric pre-release identifiers compare numerically", () => {
  assert.equal(compareSemver("1.0.0-beta.2", "1.0.0-beta.11"), -1);
});

test("pre-release precedes the normal version", () => {
  assert.equal(compareSemver("1.0.0-rc.1", "1.0.0"), -1);
});

test("build metadata is ignored", () => {
  assert.equal(compareSemver("1.0.0+build.1", "1.0.0+build.2"), 0);
});

// spec.md section 11: numeric identifiers always have lower precedence than
// non-numeric ones. "1" is numeric, "--a" is alphanumeric (ASCII lexical).
test("numeric prerelease identifier precedes alphanumeric identifier", () => {
  assert.equal(compareSemver("1.0.0-1", "1.0.0--a"), -1);
});

test("higher precedence and equality return positive and zero", () => {
  // spec.md: return 1 when a has higher precedence, 0 when equal.
  assert.equal(compareSemver("1.0.0", "1.0.0-rc.1"), 1);
  assert.equal(compareSemver("2.0.0", "1.9.9"), 1);
  assert.equal(compareSemver("1.0.0-alpha", "1.0.0-alpha"), 0);
});
