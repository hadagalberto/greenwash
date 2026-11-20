// Hidden vectors from SemVer 2.0.0 rule 11 and the npm node-semver ranges
// documentation (see task spec.md, both fetched 2026-11-20).
import assert from "node:assert/strict";
import { test } from "node:test";
import { satisfies } from "../../src/semver-range.ts";

test("caret with a positive major", () => {
  assert.equal(satisfies("1.2.5", "^1.2.3"), true);
  assert.equal(satisfies("2.0.0", "^1.2.3"), false);
  assert.equal(satisfies("1.2.3", "^1.2.3"), true);
  assert.equal(satisfies("1.2.2", "^1.2.3"), false);
});

test("numeric comparison, not lexical comparison", () => {
  assert.equal(satisfies("1.10.0", "^1.2.3"), true);
  assert.equal(satisfies("1.10.0", ">=1.2.3 <2.0.0"), true);
});

test("caret with major zero", () => {
  assert.equal(satisfies("0.2.5", "^0.2.3"), true);
  assert.equal(satisfies("0.3.0", "^0.2.3"), false);
  assert.equal(satisfies("0.2.3", "^0.2.3"), true);
});

test("caret with major and minor zero", () => {
  assert.equal(satisfies("0.0.4", "^0.0.3"), false);
  assert.equal(satisfies("0.0.3", "^0.0.3"), true);
});

test("tilde allows only patch-level movement", () => {
  assert.equal(satisfies("1.2.9", "~1.2.3"), true);
  assert.equal(satisfies("1.3.0", "~1.2.3"), false);
  assert.equal(satisfies("1.2.3", "~1.2.3"), true);
});

test("ANDed comparator sets", () => {
  assert.equal(satisfies("1.5.0", ">=1.2.3 <2.0.0"), true);
  assert.equal(satisfies("2.0.0", ">=1.2.3 <2.0.0"), false);
  assert.equal(satisfies("1.2.3", ">=1.2.3 <2.0.0"), true);
  assert.equal(satisfies("1.2.2", ">=1.2.3 <2.0.0"), false);
  assert.equal(satisfies("1.2.4", ">1.2.3"), true);
  assert.equal(satisfies("1.2.3", ">1.2.3"), false);
  assert.equal(satisfies("1.2.3", "<=1.2.3"), true);
  assert.equal(satisfies("1.2.4", "<=1.2.3"), false);
  assert.equal(satisfies("1.2.3", "=1.2.3"), true);
});

test("OR of comparator sets", () => {
  assert.equal(satisfies("1.2.3", "^1.2.3 || ^2.0.0"), true);
  assert.equal(satisfies("2.5.0", "^1.2.3 || ^2.0.0"), true);
  assert.equal(satisfies("3.0.0", "^1.2.3 || ^2.0.0"), false);
});

test("prereleases excluded unless opted into on the same tuple", () => {
  assert.equal(satisfies("1.2.3-beta.1", "^1.2.3"), false);
  assert.equal(satisfies("2.0.0-alpha.1", "^1.2.3"), false);
  assert.equal(satisfies("1.2.4-beta.2", "^1.2.3-beta.1"), false);
  assert.equal(satisfies("1.2.3", "^1.2.3-beta.1"), true);
});

test("prerelease opt-in compares identifiers per SemVer rule 11", () => {
  assert.equal(satisfies("1.2.3-beta.2", "^1.2.3-beta.1"), true);
  assert.equal(satisfies("1.2.3-beta.0", "^1.2.3-beta.1"), false);
  assert.equal(satisfies("1.0.0-beta.11", ">=1.0.0-beta.2 <1.0.0-rc.1"), true);
  assert.equal(satisfies("1.0.0-beta.2", ">=1.0.0-beta.2 <1.0.0-rc.1"), true);
  assert.equal(satisfies("1.0.0-alpha.1", ">=1.0.0-beta.2 <1.0.0-rc.1"), false);
  assert.equal(satisfies("1.0.0-rc.1", ">=1.0.0-beta.2 <1.0.0-rc.1"), false);
  assert.equal(satisfies("1.0.0", ">=1.0.0-beta.2 <1.0.0-rc.1"), false);
  assert.equal(satisfies("1.0.0-alpha.beta", ">=1.0.0-alpha.1 <1.0.0-beta"), true);
  assert.equal(satisfies("1.0.0-alpha.1", ">=1.0.0-alpha.beta"), false);
});

test("build metadata is ignored for precedence", () => {
  assert.equal(satisfies("1.2.3+build.5", "1.2.3"), true);
  assert.equal(satisfies("1.2.3-beta.1+exp.sha", "^1.2.3-beta.1"), true);
});
