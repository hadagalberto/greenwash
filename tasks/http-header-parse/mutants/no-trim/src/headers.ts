// Mutant of reference: unquoted elements are not OWS-trimmed.
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
  let startedWithQuote = false;
  let closedQuote = false;

  const finishElement = (): void => {
    if (closedQuote) result.push(buffer);
    else if (startedWithQuote) throw new Error("unterminated quoted-string");
    else if (buffer !== "") result.push(buffer);
    buffer = "";
    startedWithQuote = false;
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
      finishElement();
      continue;
    }
    if (ch === '"') {
      if (closedQuote || trimOws(buffer) !== "") throw new Error("unexpected quote");
      inQuote = true;
      startedWithQuote = true;
      continue;
    }
    if (closedQuote) {
      if (ch !== " " && ch !== "\t") throw new Error("trailing data");
      continue;
    }
    buffer += ch;
  }
  if (inQuote) throw new Error("unterminated quoted-string");
  finishElement();
  return result;
}
