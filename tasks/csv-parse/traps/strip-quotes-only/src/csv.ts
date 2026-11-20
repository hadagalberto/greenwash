// Trap: removes quote characters but does not unescape doubled quotes.
export function parseCsv(text: string): string[][] {
  if (text === "") return [];
  return text.split(/\r?\n/).map((line) =>
    line.split(",").map((field) => field.replace(/"/g, "")),
  );
}
