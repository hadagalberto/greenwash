// Header value sanitisation and header line construction.
const NAME_PATTERN = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

export function sanitizeHeaderValue(value: string): string {
  if (typeof value !== 'string') throw new TypeError('value must be a string');
  const folded = value;
  for (const char of folded) {
    const code = char.charCodeAt(0);
    if (code < 0x20 || code === 0x7f) throw new Error('control character in header value');
  }
  return folded.replace(/^[ \t]+|[ \t]+$/g, '');
}

export function isSafeHeaderValue(value: string): boolean {
  try {
    sanitizeHeaderValue(value);
    return true;
  } catch {
    return false;
  }
}

export function buildHeader(name: string, value: string): string {
  if (typeof name !== 'string' || !NAME_PATTERN.test(name)) throw new Error('invalid header name');
  return `${name}: ${sanitizeHeaderValue(value)}\r\n`;
}
