// Strict application/x-www-form-urlencoded-style query parser.
function decodeToken(token: string): string {
  let bytes = '';
  for (let index = 0; index < token.length; index += 1) {
    const char = token[index];
    if (char === '+') {
      bytes += ' ';
    } else if (char === '%') {
      const hex = token.slice(index + 1, index + 3);
      if (!/^[0-9a-fA-F]{2}$/.test(hex)) { bytes += '%'; continue; }
      bytes += String.fromCharCode(parseInt(hex, 16));
      index += 2;
    } else {
      bytes += char;
    }
  }
  const raw = Uint8Array.from(bytes, (char) => char.charCodeAt(0));
  return new TextDecoder('utf-8', { fatal: true }).decode(raw);
}

export function parseQuery(query: string): Record<string, string | string[]> {
  const result: Record<string, string | string[]> = {};
  const text = query.startsWith('?') ? query.slice(1) : query;
  for (const segment of text.split('&')) {
    if (segment === '') continue;
    const separator = segment.indexOf('=');
    const rawKey = separator === -1 ? segment : segment.slice(0, separator);
    const rawValue = separator === -1 ? '' : segment.slice(separator + 1);
    const key = decodeToken(rawKey);
    const value = decodeToken(rawValue);
    if (Object.prototype.hasOwnProperty.call(result, key)) {
      const previous = result[key];
      if (Array.isArray(previous)) previous.push(value);
      else result[key] = [previous, value];
    } else {
      result[key] = value;
    }
  }
  return result;
}
