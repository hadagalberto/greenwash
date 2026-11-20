// Skeleton: returns values unchanged.
export function sanitizeHeaderValue(value: string): string {
  return value;
}

export function isSafeHeaderValue(_value: string): boolean {
  return true;
}

export function buildHeader(name: string, value: string): string {
  return `${name}: ${value}\r\n`;
}
