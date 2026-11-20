// Mutant of reference: OWS is trimmed from quoted content too.
function trimOws(text: string): string {
  let start = 0;
  let end = text.length;
  while (start < end && (text[start] === " " || text[start] === "\t")) start++;
  while (end > start && (text[end - 1] === " " || text[end - 1] === "\t")) end--;
  return text.slice(start, end);
}

export function parseHeaderValue(value: string): string[] {
  const result: string[] = [];
  let buffer = "";
  let inQuote = false;
  let quoted = false;
  let closedQuote = false;

  const finish = (): void => {
    if (quoted || closedQuote) {
      const element = trimOws(buffer);
      if (element !== "") result.push(element);
    } else {
      const element = trimOws(buffer);
      if (element !== "") result.push(element);
    }
    buffer = "";
    quoted = false;
    closedQuote = false;
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
        closedQuote = true;
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
      if (closedQuote || trimOws(buffer) !== "") throw new Error("unexpected quote");
      inQuote = true;
      quoted = true;
      continue;
    }
    if (closedQuote) {
      if (ch !== " " && ch !== "\t") throw new Error("trailing data");
      continue;
    }
    buffer += ch;
  }
  if (inQuote) throw new Error("unterminated quoted-string");
  finish();
  return result;
}
