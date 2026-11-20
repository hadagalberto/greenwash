# SemVer version range satisfaction

Implement `src/semver-range.ts` exporting:

```ts
export function satisfies(version: string, range: string): boolean;
```

All `version` and range component strings are valid SemVer 2.0.0 strings; no
validation of malformed input is required. Build metadata is ignored for
precedence. Sources, fetched 2026-11-20:

- https://semver.org/spec/v2.0.0.html — SemVer 2.0.0, especially rule 11
  (precedence: numeric major/minor/patch; prerelease lower than release;
  dot-separated identifier comparison: numeric numerically, alphanumeric
  lexically in ASCII order, numeric lower than alphanumeric, longer set of
  identifiers higher when all preceding ones are equal).
- https://github.com/npm/node-semver#ranges — comparator sets, `||`, caret,
  tilde, and the prerelease opt-in rule.

## Supported range syntax

| Range | Meaning |
| --- | --- |
| `X.Y.Z` | exactly `X.Y.Z` |
| `^X.Y.Z`, X > 0 | `>=X.Y.Z <(X+1).0.0` |
| `^0.Y.Z`, Y > 0 | `>=0.Y.Z <0.(Y+1).0` |
| `^0.0.Z` | exactly `0.0.Z` (upper bound `<0.0.(Z+1)`) |
| `~X.Y.Z` | `>=X.Y.Z <X.(Y+1).0` |
| `>=A.B.C`, `>A.B.C`, `<=A.B.C`, `<A.B.C`, `=A.B.C` | the corresponding comparison |
| `A B` | space-separated comparators are ANDed |
| `R1 || R2` | OR: satisfy either side |

The comparison of numeric components is numeric, never lexical: `1.10.0` is
greater than `1.2.3`.

## Prerelease rule

A version with a prerelease identifier (for example `1.2.3-beta.1`) satisfies a
comparator set **only if** at least one comparator in that set has a prerelease
identifier with the same major.minor.patch tuple. Otherwise it does not
satisfy the set, even if its precedence would otherwise be inside the bounds.
When a comparator does carry a prerelease on that tuple, compare prerelease
identifiers following SemVer 2.0.0 rule 11. A normal (non-prerelease) version
may satisfy a range whose bounds include prereleases, provided its precedence
is inside the bounds.

## Vectors

| version | range | result |
| --- | --- | --- |
| `1.2.5` | `^1.2.3` | true |
| `2.0.0` | `^1.2.3` | false |
| `0.2.5` | `^0.2.3` | true |
| `0.3.0` | `^0.2.3` | false |
| `0.0.4` | `^0.0.3` | false |
| `1.2.9` | `~1.2.3` | true |
| `1.3.0` | `~1.2.3` | false |
| `1.5.0` | `>=1.2.3 <2.0.0` | true |
| `2.0.0` | `>=1.2.3 <2.0.0` | false |
| `1.2.3` | `^1.2.3 \|\| ^2.0.0` | true |
| `1.2.3-beta.1` | `^1.2.3` | false |
| `1.2.3-beta.2` | `^1.2.3-beta.1` | true |
| `1.10.0` | `^1.2.3` | true |

SemVer rule 11 ordering example: `1.0.0-alpha < 1.0.0-alpha.1 <
1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 <
1.0.0`.
