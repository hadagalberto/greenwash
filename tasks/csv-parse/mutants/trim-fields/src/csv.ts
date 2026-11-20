// RFC 4180-style CSV parser: quoted fields, embedded newlines, doubled quotes.
// Source: https://www.rfc-editor.org/rfc/rfc4180.txt (section 2)

export function parseCsv(text: string): string[][] {
  if (text === "") return [];
  const records: string[][] = [];
  let record: string[] = [];
  let field = "";
  let inQuotes = false;
  let fieldStarted = false;
  let i = 0;

  while (i < text.length) {
    const ch = text[i] ?? "";
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i += 1;
        continue;
      }
      field += ch;
      fieldStarted = true;
      i += 1;
      continue;
    }
    if (ch === '"' && !fieldStarted) {
      inQuotes = true;
      fieldStarted = true;
      i += 1;
      continue;
    }
    if (ch === ",") {
      record.push(field);
      field = "";
      fieldStarted = false;
      i += 1;
      continue;
    }
    if (ch === "\r" || ch === "\n") {
      record.push(field);
      records.push(record);
      record = [];
      field = "";
      fieldStarted = false;
      if (ch === "\r" && text[i + 1] === "\n") i += 2;
      else i += 1;
      continue;
    }
    field += ch;
    fieldStarted = true;
    i += 1;
  }

  if (inQuotes) throw new Error("unterminated quoted field");
  if (fieldStarted || record.length > 0) {
    record.push(field.trim());
    records.push(record);
  }
  return records;
}
