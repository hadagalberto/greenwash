// Correct parser: RFC 9110 sections 5.5, 5.6.1, 5.6.2 and 5.6.4.
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
    if (closedQuote) {
      result.push(buffer);
    } else if (startedWithQuote) {
      throw new Error("unterminated quoted-string");
    } else {
      const element = trimOws(buffer);
      if (element !== "") result.push(element);
    }
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
      if (closedQuote || trimOws(buffer) !== "") {
        throw new Error("unexpected quote");
      }
      // OWS before the opening quote is not part of the quoted value.
      buffer = "";
      inQuote = true;
      startedWithQuote = true;
      continue;
    }
    if (closedQuote) {
      if (ch !== " " && ch !== "\t") throw new Error("trailing data after quoted-string");
      continue;
    }
    buffer += ch;
  }
  if (inQuote) throw new Error("unterminated quoted-string");
  finishElement();
  return result;
}
