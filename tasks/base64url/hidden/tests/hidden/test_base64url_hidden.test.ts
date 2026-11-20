// Hidden vectors from RFC 4648 sections 5 and 10 (see task spec.md).
import assert from "node:assert/strict";
import { test } from "node:test";
import { decodeUrl, encodeUrl } from "../../src/base64url.ts";

test("RFC 4648 empty vector", () => {
  assert.equal(encodeUrl(new Uint8Array()), "");
});

test("RFC 4648 single byte vector", () => {
  assert.equal(encodeUrl(Uint8Array.of(0x66)), "Zg");
});

test("URL-safe alphabet check vector", () => {
  assert.equal(encodeUrl(Uint8Array.of(0xfb, 0xff, 0x00)), "-_8A");
});

test("decodes the URL-safe check vector", () => {
  assert.deepEqual(decodeUrl("-_8A"), Uint8Array.of(0xfb, 0xff, 0x00));
});

test("rejects standard base64 characters outside the URL-safe alphabet", () => {
  assert.throws(() => decodeUrl("AB+C"), Error);
});
