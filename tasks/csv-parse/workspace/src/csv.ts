// RFC 4180-style CSV parser — incomplete starting point.
// See spec.md for quoting, line-ending and trailing-record rules.

export function parseCsv(text: string): string[][] {
  // Handles only the simplest unquoted, single-line case so far.
  if (text === "") return [];
  return [text.split(",")];
}
