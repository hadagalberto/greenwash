// Mutant: decoder also accepts the standard base64 + and / characters.
const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

export function encodeUrl(data: Uint8Array): string {
  let out = "";
  for (let i = 0; i < data.length; i += 3) {
    const b0 = data[i] ?? 0;
    const b1 = i + 1 < data.length ? (data[i + 1] ?? 0) : 0;
    const b2 = i + 2 < data.length ? (data[i + 2] ?? 0) : 0;
    const group = (b0 << 16) | (b1 << 8) | b2;
    out += ALPHABET[(group >>> 18) & 63];
    out += ALPHABET[(group >>> 12) & 63];
    if (i + 1 < data.length) out += ALPHABET[(group >>> 6) & 63];
    if (i + 2 < data.length) out += ALPHABET[group & 63];
  }
  return out;
}

export function decodeUrl(text: string): Uint8Array {
  const values: number[] = [];
  for (const char of text) {
    let index = ALPHABET.indexOf(char);
    if (index < 0 && char === "+") index = 62;
    if (index < 0 && char === "/") index = 63;
    if (index < 0) throw new Error(`invalid base64url character: ${char}`);
    values.push(index);
  }
  if (values.length % 4 === 1) throw new Error("invalid base64url length");
  const bytes: number[] = [];
  for (let i = 0; i < values.length; i += 4) {
    const chunk = values.slice(i, i + 4);
    const group = ((chunk[0] ?? 0) << 18) | ((chunk[1] ?? 0) << 12) | ((chunk[2] ?? 0) << 6) | (chunk[3] ?? 0);
    bytes.push((group >>> 16) & 255);
    if (chunk.length >= 3) bytes.push((group >>> 8) & 255);
    if (chunk.length === 4) bytes.push(group & 255);
  }
  return new Uint8Array(bytes);
}
