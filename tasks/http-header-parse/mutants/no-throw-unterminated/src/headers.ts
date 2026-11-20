// Mutant of reference: an unterminated quoted-string is accepted as data.
function trimOws(text: string): string {
  return text.replace(/^[ \t]+/, "").replace(/[ \t]+$/, "");
}

export function parseHeaderValue(value: string): string[] {
  const result: string[] = [];
  let buffer = "";
  let inQuote = false;
  let quoted = false;
  let closedQuote = false;

  const finish = (): void => {
    if (quoted || closedQuote) result.push(buffer);
    else {
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
  finish();
  return result;
}
