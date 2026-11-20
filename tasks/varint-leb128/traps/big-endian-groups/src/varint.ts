// Trap: emits the 7-bit groups in big-endian order (wrong for LEB128).
export function encodeVarint(value: number): number[] {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError("value must be a non-negative safe integer");
  }
  const groups: number[] = [];
  let remaining = value;
  do {
    groups.push(remaining % 128);
    remaining = Math.floor(remaining / 128);
  } while (remaining !== 0);
  groups.reverse();
  return groups.map((group, index) =>
    index === groups.length - 1 ? group : group | 0x80,
  );
}

export function decodeVarint(bytes: number[]): number {
  if (bytes.length === 0) throw new Error("empty varint");
  let result = 0;
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i] ?? 0;
    result = result * 128 + (byte & 0x7f);
    if ((byte & 0x80) === 0) {
      if (i !== bytes.length - 1) throw new Error("trailing bytes after varint");
      return result;
    }
  }
  throw new Error("missing terminator");
}
