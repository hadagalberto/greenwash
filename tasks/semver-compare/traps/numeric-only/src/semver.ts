// Trap: plausible mistake — compares only major.minor.patch, ignores pre-release.
export function compareSemver(a: string, b: string): number {
  const core = (version: string): number[] =>
    (version.split("+", 1)[0] ?? version)
      .split("-", 1)[0]
      .split(".")
      .map((part) => Number(part));
  const left = core(a);
  const right = core(b);
  for (let i = 0; i < 3; i++) {
    const difference = (left[i] ?? 0) - (right[i] ?? 0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  return 0;
}
