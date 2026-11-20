// Mutant: build metadata is (incorrectly) included in precedence.
function parts(version: string): { core: number[]; rest: string } {
  const core = version
    .split("+", 1)[0]
    ?.split("-", 1)[0]
    ?.split(".")
    .map((part) => Number(part)) ?? [0, 0, 0];
  const plus = version.indexOf("+");
  return { core, rest: plus < 0 ? "" : version.slice(plus + 1) };
}

export function compareSemver(a: string, b: string): number {
  const left = parts(a);
  const right = parts(b);
  for (let i = 0; i < 3; i++) {
    const difference = (left.core[i] ?? 0) - (right.core[i] ?? 0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  if (left.rest === right.rest) return 0;
  return left.rest < right.rest ? -1 : 1;
}
