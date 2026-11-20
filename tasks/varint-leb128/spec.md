# Unsigned LEB128 varint codec

Implement `src/varint.ts` exporting:

```ts
export function encodeVarint(value: number): number[];
export function decodeVarint(bytes: number[]): number;
```

The encoding is unsigned LEB128 (also called a base-128 varint), as described by
Wikipedia's LEB128 article (sections "Unsigned LEB128" and "C-like pseudocode")
and Google's Protocol Buffers encoding guide (section "Base 128 Varints").
Both sources were fetched 2026-11-20:

- https://en.wikipedia.org/wiki/LEB128
- https://protobuf.dev/programming-guides/encoding/#varints

## Format

- Split the non-negative integer into groups of 7 bits.
- Emit one byte per group, **least-significant group first** (little-endian).
- The low 7 bits of each byte carry the group. Bit 7 (`0x80`) is the
  continuation flag: set it on every byte except the most-significant (last)
  byte.
- Zero is the single byte `0x00`.
- This task requires the **canonical** encoding: the last byte's 7-bit payload
  must be non-zero, except for the single-byte encoding of zero. `0x80 0x00`
  is therefore not a valid encoding of zero.

## `encodeVarint(value: number): number[]`

- Accept only non-negative safe integers (`Number.isSafeInteger(value) &&
  value >= 0`). Throw a `RangeError` for negatives, non-integers, `NaN`,
  infinities, and any value greater than `Number.MAX_SAFE_INTEGER`.
- Return the canonical byte array as plain numbers in `[0, 255]`.

## `decodeVarint(bytes: number[]): number`

- Decode one whole unsigned LEB128 value from `bytes`.
- Throw an `Error` (any subclass is acceptable) when:
  - the input is empty;
  - a byte lacks the continuation flag before the end (missing terminator);
  - the final byte has a zero 7-bit payload and the encoding is longer than one
    byte (overlong / non-canonical encoding);
  - bytes remain after the terminating byte (extra trailing data);
  - the decoded value exceeds `Number.MAX_SAFE_INTEGER`.
- Otherwise return the decoded number.

Use arithmetic (`payload * 2 ** shift`), not JavaScript bitwise shifts, when
accumulating the result: bitwise operators truncate to 32 bits.

## Worked vectors

| value | canonical bytes (hex) |
| --- | --- |
| 0 | `00` |
| 1 | `01` |
| 127 | `7f` |
| 128 | `80 01` |
| 300 | `ac 02` |
| 16383 | `ff 7f` |
| 16384 | `80 80 01` |
| 624485 | `e5 8e 26` |

`624485 -> e5 8e 26` is the worked example in the Wikipedia article.
`150 -> 96 01` is the worked example in the Protocol Buffers guide. For 16383,
the two 7-bit groups are both `0x7f`, so the first byte carries the continuation
flag: `ff 7f` (the sequence `7f 7f` is not canonical because the first byte
terminates the varint).

Examples:

```ts
encodeVarint(300);                // [0xac, 0x02]
decodeVarint([0xe5, 0x8e, 0x26]); // 624485
decodeVarint([0x80, 0x00]);       // throws Error (overlong)
decodeVarint([0x80]);             // throws Error (missing terminator)
encodeVarint(-1);                 // throws RangeError
```

Wikipedia notes that WebAssembly permits alternate (overlong) encodings of
zero; this task does not — canonical output and strict decoding are required.
