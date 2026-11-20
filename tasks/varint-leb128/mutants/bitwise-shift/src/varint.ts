// Mutant: accumulates with a 32-bit bitwise shift instead of arithmetic.
const MAX_SAFE = Number.MAX_SAFE_INTEGER;

export function encodeVarint(value: number): number[] {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError("value must be a non-negative safe integer");
  }
  const out: number[] = [];
  let remaining = value;
  do {
    let byte = remaining % 128;
    remaining = Math.floor(remaining / 128);
    if (remaining !== 0) byte |= 0x80;
    out.push(byte);
  } while (remaining !== 0);
  return out;
}

export function decodeVarint(bytes: number[]): number {
  if (bytes.length === 0) throw new Error("empty varint");
  let result = 0;
  let shift = 0;
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i] ?? 0;
    const payload = byte & 0x7f;
    if (payload !== 0) {
      if (shift > 53) throw new Error("varint exceeds MAX_SAFE_INTEGER");
      result += payload << shift;
      if (result > MAX_SAFE) throw new Error("varint exceeds MAX_SAFE_INTEGER");
    }
    if ((byte & 0x80) === 0) {
      if (i !== bytes.length - 1) throw new Error("trailing bytes after varint");
      if (i !== 0 && payload === 0) throw new Error("overlong encoding");
      return result;
    }
    shift += 7;
  }
  throw new Error("missing terminator");
}
