// Trap: splits on newlines and commas, ignoring quoting entirely.
export function parseCsv(text: string): string[][] {
  if (text === "") return [];
  return text.split(/\r?\n/).map((line) => line.split(","));
}
