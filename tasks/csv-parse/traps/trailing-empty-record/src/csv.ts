// Trap: appends an extra empty record whenever the text ends with a newline.
export function parseCsv(text: string): string[][] {
  if (text === "") return [];
  const rows = text.split(/\r?\n/).map((line) => line.split(","));
  if (/\r?\n$/.test(text)) rows.push([]);
  return rows;
}
