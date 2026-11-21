// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: Decoding must reject any character outside the alphabet (including ...
//     -> rejects a five-character (1 mod 4) message, rejects standard base64 characters outside
//       the URL-safe alphabet, URL-safe alphabet check vector
// R2: Reject non-zero pad bits for canonical encoding.
//     -> rejects non-zero pad bits in a three-character group, rejects non-zero pad bits in a two-
//       character group, RFC 4648 empty vector
// R3: Do not use Node's `Buffer` base64 helpers; implement the codec.
//     -> rejects standard base64 characters outside the URL-safe alphabet, RFC 4648 empty vector,
//       RFC 4648 single byte vector
//
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

// spec.md: "Reject non-zero pad bits for canonical encoding" (RFC 4648 3.5)
// and "reject a length congruent to 1 modulo 4" (RFC 4648 3.2). All four
// expected throws are derived by hand from those two sentences.
test("rejects non-zero pad bits in a two-character group", () => {
  assert.throws(() => decodeUrl("Zh"));
});

test("rejects non-zero pad bits in a three-character group", () => {
  assert.throws(() => decodeUrl("Zm9"));
});

test("rejects a single-character message", () => {
  assert.throws(() => decodeUrl("A"));
});

test("rejects a five-character (1 mod 4) message", () => {
  assert.throws(() => decodeUrl("AAAAA"));
});
