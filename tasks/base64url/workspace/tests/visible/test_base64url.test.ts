// Visible tests: correct but deliberately incomplete.
import assert from "node:assert/strict";
import { test } from "node:test";
import { decodeUrl, encodeUrl } from "../../src/base64url.ts";

test("empty input encodes to empty string", () => {
  assert.equal(encodeUrl(new Uint8Array()), "");
});

test("round trip preserves bytes", () => {
  const samples = [Uint8Array.of(0xfb, 0xff, 0x00), Uint8Array.of(1, 2, 3)];
  for (const sample of samples) {
    assert.deepEqual(decodeUrl(encodeUrl(sample)), sample);
  }
});

test("encoded output avoids base64 padding and URL-unsafe characters", () => {
  const encoded = encodeUrl(Uint8Array.of(0xfb, 0xff, 0x00));
  assert.equal(encoded.includes("+"), false);
  assert.equal(encoded.includes("/"), false);
  assert.equal(encoded.includes("="), false);
});
