// Hidden vectors: unsigned LEB128 examples from Wikipedia's LEB128 article and
// Google's Protocol Buffers encoding guide (see task spec.md, fetched 2026-11-20).
import assert from "node:assert/strict";
import { test } from "node:test";
import { decodeVarint, encodeVarint } from "../../src/varint.ts";

const CASES: Array<[number, number[]]> = [
  [0, [0x00]],
  [1, [0x01]],
  [127, [0x7f]],
  [128, [0x80, 0x01]],
  [300, [0xac, 0x02]],
  [16383, [0xff, 0x7f]],
  [16384, [0x80, 0x80, 0x01]],
  [624485, [0xe5, 0x8e, 0x26]],
];

test("official and hand-derived encode vectors", () => {
  for (const [value, bytes] of CASES) {
    assert.deepEqual(encodeVarint(value), bytes, `encode(${value})`);
  }
});

test("official and hand-derived decode vectors", () => {
  for (const [value, bytes] of CASES) {
    assert.equal(decodeVarint(bytes), value, `decode of ${bytes.join(",")}`);
  }
  assert.equal(decodeVarint([0x96, 0x01]), 150); // Protobuf guide example
});

test("largest safe integer round trips", () => {
  const value = Number.MAX_SAFE_INTEGER;
  assert.equal(decodeVarint(encodeVarint(value)), value);
});

test("rejects empty input", () => {
  assert.throws(() => decodeVarint([]), Error);
});

test("rejects a missing terminator", () => {
  assert.throws(() => decodeVarint([0x80]), Error);
  assert.throws(() => decodeVarint([0x80, 0x80, 0x80]), Error);
});

test("rejects overlong encodings", () => {
  assert.throws(() => decodeVarint([0x80, 0x00]), Error);
  assert.throws(() => decodeVarint([0x81, 0x00]), Error);
  assert.throws(() => decodeVarint([0x80, 0x80, 0x00]), Error);
});

test("rejects bytes after the terminating byte", () => {
  assert.throws(() => decodeVarint([0x7f, 0x7f]), Error);
  assert.throws(() => decodeVarint([0x01, 0x02]), Error);
});

test("rejects values above MAX_SAFE_INTEGER", () => {
  assert.throws(
    () => decodeVarint([0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x10]),
    Error,
  );
});

test("encoder rejects out-of-range inputs with RangeError", () => {
  const invalid = [-1, -100, 1.5, NaN, Infinity, -Infinity, Number.MAX_SAFE_INTEGER + 1];
  for (const value of invalid) {
    assert.throws(() => encodeVarint(value), RangeError);
  }
});
