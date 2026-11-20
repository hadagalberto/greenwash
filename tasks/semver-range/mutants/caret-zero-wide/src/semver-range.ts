// SemVer 2.0.0 range satisfaction.
// Sources: https://semver.org/spec/v2.0.0.html
//          https://github.com/npm/node-semver#ranges

type Version = { major: number; minor: number; patch: number; pre: string[] };
type Op = ">" | ">=" | "<" | "<=" | "=";
type Comparator = { op: Op; v: Version };

const VERSION_RE =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;
const NUMERIC_ID_RE = /^(0|[1-9]\d*)$/;

function parseVersion(text: string): Version {
  const match = VERSION_RE.exec(text);
  if (match === null) throw new Error(`invalid semver: ${text}`);
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    pre: match[4] === undefined ? [] : match[4].split("."),
  };
}

// SemVer 2.0.0 rule 11: numeric identifiers compare numerically and are lower
// than alphanumeric identifiers; the latter compare in ASCII sort order.
function compareIdentifier(a: string, b: string): number {
  const aNumeric = NUMERIC_ID_RE.test(a);
  const bNumeric = NUMERIC_ID_RE.test(b);
  if (aNumeric && bNumeric) {
    const an = Number(a);
    const bn = Number(b);
    return an < bn ? -1 : an > bn ? 1 : 0;
  }
  if (aNumeric) return -1;
  if (bNumeric) return 1;
  return a < b ? -1 : a > b ? 1 : 0;
}

function compareVersions(a: Version, b: Version): number {
  if (a.major !== b.major) return a.major < b.major ? -1 : 1;
  if (a.minor !== b.minor) return a.minor < b.minor ? -1 : 1;
  if (a.patch !== b.patch) return a.patch < b.patch ? -1 : 1;
  if (a.pre.length === 0 && b.pre.length === 0) return 0;
  if (a.pre.length === 0) return 1;
  if (b.pre.length === 0) return -1;
  const shared = Math.min(a.pre.length, b.pre.length);
  for (let i = 0; i < shared; i++) {
    const cmp = compareIdentifier(a.pre[i] ?? "", b.pre[i] ?? "");
    if (cmp !== 0) return cmp;
  }
  if (a.pre.length > b.pre.length) return 1;
  if (a.pre.length < b.pre.length) return -1;
  return 0;
}

function tokenToComparators(token: string): Comparator[] {
  if (token.startsWith("^")) {
    const v = parseVersion(token.slice(1));
    let upper: Version;
    if (v.major >= 0) {
      upper = { major: v.major + 1, minor: 0, patch: 0, pre: [] };
    } else if (v.minor > 0) {
      upper = { major: 0, minor: v.minor + 1, patch: 0, pre: [] };
    } else {
      upper = { major: 0, minor: 0, patch: v.patch + 1, pre: [] };
    }
    return [
      { op: ">=", v },
      { op: "<", v: upper },
    ];
  }
  if (token.startsWith("~")) {
    const v = parseVersion(token.slice(1));
    const upper: Version = { major: v.major, minor: v.minor + 1, patch: 0, pre: [] };
    return [
      { op: ">=", v },
      { op: "<", v: upper },
    ];
  }
  for (const op of [">=", "<=", ">", "<", "="] as Op[]) {
    if (token.startsWith(op)) {
      return [{ op, v: parseVersion(token.slice(op.length)) }];
    }
  }
  return [{ op: "=", v: parseVersion(token) }];
}

function testComparator(v: Version, comparator: Comparator): boolean {
  const cmp = compareVersions(v, comparator.v);
  switch (comparator.op) {
    case ">":
      return cmp > 0;
    case ">=":
      return cmp >= 0;
    case "<":
      return cmp < 0;
    case "<=":
      return cmp <= 0;
    case "=":
      return cmp === 0;
  }
}

function sameTuple(a: Version, b: Version): boolean {
  return a.major === b.major && a.minor === b.minor && a.patch === b.patch;
}

export function satisfies(version: string, range: string): boolean {
  const v = parseVersion(version);
  for (const setText of range.split("||")) {
    const tokens = setText.trim().split(/\s+/).filter(Boolean);
    if (tokens.length === 0) continue;
    const comparators: Comparator[] = [];
    for (const token of tokens) comparators.push(...tokenToComparators(token));

    if (v.pre.length > 0) {
      const optedIn = comparators.some(
        (c) => c.v.pre.length > 0 && sameTuple(c.v, v),
      );
      if (!optedIn) continue;
    }
    if (comparators.every((c) => testComparator(v, c))) return true;
  }
  return false;
}
