// SemVer range satisfaction — incomplete starting point.
// See spec.md for the required syntax, precedence rules and vectors.

export function satisfies(version: string, range: string): boolean {
  // Handles exact equality only so far.
  return version === range;
}
