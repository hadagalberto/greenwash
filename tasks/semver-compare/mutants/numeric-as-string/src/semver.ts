// Mutant: numeric pre-release identifiers compared lexically ("11" < "2").
function pre(version: string): string {
  const withoutBuild = version.split("+", 1)[0] ?? version;
  const dash = withoutBuild.indexOf("-");
  return dash < 0 ? "" : withoutBuild.slice(dash + 1);
}

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
  const lp = pre(a);
  const rp = pre(b);
  if (lp === rp) return 0;
  if (lp === "") return 1;
  if (rp === "") return -1;
  return lp < rp ? -1 : 1;
}
