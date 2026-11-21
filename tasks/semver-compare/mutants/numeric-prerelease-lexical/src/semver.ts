// Semantic Versioning 2.0.0 section 11 precedence.
// https://semver.org/spec/v2.0.0.html

interface ParsedVersion {
  core: [number, number, number];
  prerelease: string[];
}

function parse(version: string): ParsedVersion {
  const withoutBuild = version.split("+", 1)[0] ?? version;
  const dash = withoutBuild.indexOf("-");
  const coreText = dash < 0 ? withoutBuild : withoutBuild.slice(0, dash);
  const preText = dash < 0 ? "" : withoutBuild.slice(dash + 1);
  const parts = coreText.split(".");
  return {
    core: [Number(parts[0] ?? 0), Number(parts[1] ?? 0), Number(parts[2] ?? 0)],
    prerelease: preText === "" ? [] : preText.split("."),
  };
}

function sign(value: number): number {
  return value < 0 ? -1 : value > 0 ? 1 : 0;
}

export function compareSemver(a: string, b: string): number {
  const left = parse(a);
  const right = parse(b);
  for (let i = 0; i < 3; i++) {
    const difference = (left.core[i] ?? 0) - (right.core[i] ?? 0);
    if (difference !== 0) return sign(difference);
  }
  if (left.prerelease.length === 0 && right.prerelease.length === 0) return 0;
  if (left.prerelease.length === 0) return 1;
  if (right.prerelease.length === 0) return -1;

  const shared = Math.min(left.prerelease.length, right.prerelease.length);
  for (let i = 0; i < shared; i++) {
    const x = left.prerelease[i] ?? "";
    const y = right.prerelease[i] ?? "";
    const xNumeric = /^\d+$/.test(x);
    const yNumeric = /^\d+$/.test(y);
    let difference: number;
    if (xNumeric && yNumeric) difference = x < y ? -1 : x > y ? 1 : 0;
    else if (xNumeric !== yNumeric) difference = xNumeric ? -1 : 1;
    else difference = x < y ? -1 : x > y ? 1 : 0;
    if (difference !== 0) return sign(difference);
  }
  return sign(left.prerelease.length - right.prerelease.length);
}
