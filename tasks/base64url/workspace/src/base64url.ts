// URL-safe unpadded base64 codec (incomplete starting point).

export function encodeUrl(data: Uint8Array): string {
  // Only the empty input is handled so far.
  return data.length === 0 ? "" : "?";
}

export function decodeUrl(text: string): Uint8Array {
  return new Uint8Array();
}
