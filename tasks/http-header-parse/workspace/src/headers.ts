// HTTP field-value list parser (incomplete starting point).

export function parseHeaderValue(value: string): string[] {
  // Handles only the simplest unquoted case so far.
  return value.trim() === "" ? [] : [value.trim()];
}
