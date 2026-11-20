// Unsigned LEB128 varint codec — incomplete starting point.
// See spec.md for the required behaviour and official vectors.

export function encodeVarint(value: number): number[] {
  // Only the one-byte cases are handled so far.
  if (value === 0) return [0];
  if (value === 1) return [1];
  throw new Error("unsupported input");
}

export function decodeVarint(bytes: number[]): number {
  if (bytes.length === 1 && (bytes[0] === 0 || bytes[0] === 1 || bytes[0] === 4)) {
    return bytes[0] ?? 0;
  }
  throw new Error("unsupported input");
}
