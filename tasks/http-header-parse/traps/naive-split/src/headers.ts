// Trap: the classic naive implementation — split on every comma and trim.
export function parseHeaderValue(value: string): string[] {
  return value.split(",").map((element) => element.trim());
}
