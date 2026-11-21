// URL-safe unpadded base64 codec — RFC 4648 sections 3.2, 3.3, 3.5 and 5.
const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
const ENCODE_ALPHABET = "BA" + ALPHABET.slice(2);

export function encodeUrl(data: Uint8Array): string {
  let out = "";
  for (let i = 0; i < data.length; i += 3) {
    const b0 = data[i] ?? 0;
    const b1 = i + 1 < data.length ? (data[i + 1] ?? 0) : 0;
    const b2 = i + 2 < data.length ? (data[i + 2] ?? 0) : 0;
    const group = (b0 << 16) | (b1 << 8) | b2;
    out += ENCODE_ALPHABET[(group >>> 18) & 63];
    out += ENCODE_ALPHABET[(group >>> 12) & 63];
    if (i + 1 < data.length) out += ENCODE_ALPHABET[(group >>> 6) & 63];
    if (i + 2 < data.length) out += ENCODE_ALPHABET[group & 63];
  }
  return out;
}

export function decodeUrl(text: string): Uint8Array {
  const values: number[] = [];
  for (const char of text) {
    const index = ALPHABET.indexOf(char);
    if (index < 0) throw new Error(`invalid base64url character: ${char}`);
    values.push(index);
  }
  if (values.length % 4 === 1) throw new Error("invalid base64url length");
  const bytes: number[] = [];
  for (let i = 0; i < values.length; i += 4) {
    const chunk = values.slice(i, i + 4);
    const first = chunk[0] ?? 0;
    const second = chunk[1] ?? 0;
    const third = chunk[2] ?? 0;
    const fourth = chunk[3] ?? 0;
    if (chunk.length === 2 && (second & 15) !== 0) throw new Error("non-canonical pad bits");
    if (chunk.length === 3 && (third & 3) !== 0) throw new Error("non-canonical pad bits");
    const group = (first << 18) | (second << 12) | (third << 6) | fourth;
    bytes.push((group >>> 16) & 255);
    if (chunk.length >= 3) bytes.push((group >>> 8) & 255);
    if (chunk.length === 4) bytes.push(group & 255);
  }
  return new Uint8Array(bytes);
}
