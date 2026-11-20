// Trap: correct quote handling and unescaping, but empty list elements are kept.
function trimOws(text: string): string {
  return text.replace(/^[ \t]+/, "").replace(/[ \t]+$/, "");
}

export function parseHeaderValue(value: string): string[] {
  const result: string[] = [];
  let buffer = "";
  let inQuote = false;
  let quoted = false;

  const finish = (): void => {
    if (quoted) result.push(buffer);
    else result.push(trimOws(buffer));
    buffer = "";
    quoted = false;
  };

  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i] ?? "";
    if (inQuote) {
      if (ch === "\\") {
        if (i + 1 >= value.length) throw new Error("dangling backslash");
        buffer += value[i + 1];
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
      if (trimOws(buffer) !== "") throw new Error("unexpected quote");
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
