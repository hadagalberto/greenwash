// Trap: understands quoting for delimiters but never removes quoted-pair backslashes
// and does not strip OWS around a quoted element.
export function parseHeaderValue(value: string): string[] {
  const result: string[] = [];
  let buffer = "";
  let inQuote = false;
  let quoted = false;

  const finish = (): void => {
    if (quoted) result.push(buffer);
    else if (buffer.trim() !== "") result.push(buffer.trim());
    buffer = "";
    quoted = false;
  };

  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i] ?? "";
    if (inQuote) {
      if (ch === "\\" && i + 1 < value.length) {
        buffer += ch + (value[i + 1] ?? "");
        i += 1;
      } else if (ch === '"') {
        inQuote = false;
      } else {
        buffer += ch;
      }
      continue;
    }
    if (ch === ",") {
      finish();
      continue;
    }
    if (ch === '"') {
      inQuote = true;
      quoted = true;
      continue;
    }
    buffer += ch;
  }
  if (inQuote) throw new Error("unterminated quoted-string");
  finish();
  return result;
}
