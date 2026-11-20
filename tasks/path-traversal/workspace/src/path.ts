// Safe path join (incomplete starting point).

export function safeJoin(base: string, userPath: string): string | null {
  return `${base}/${userPath}`;
}
