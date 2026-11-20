// SemVer precedence comparison (incomplete starting point).

export function compareSemver(a: string, b: string): number {
  // Placeholder behaviour: raw string order is not SemVer precedence.
  return a < b ? -1 : a > b ? 1 : 0;
}
