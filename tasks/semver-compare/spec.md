# SemVer 2.0.0 precedence

Implement `compareSemver(a: string, b: string): number` in `src/semver.ts`.
Return `-1` if `a` has lower precedence than `b`, `0` if they have equal
precedence, and `1` if `a` has higher precedence.

Follow **Semantic Versioning 2.0.0, section 11 (Precedence)** exactly:

1. split into major, minor, patch and pre-release identifiers (build metadata is
   ignored when determining precedence);
2. compare major, minor and patch numerically, left to right;
3. when those are equal, a version **without** pre-release has higher precedence
   than one with a pre-release;
4. for two pre-releases, compare dot-separated identifiers left to right:
   - all-digit identifiers are compared numerically;
   - identifiers with letters or hyphens are compared lexically in ASCII order;
   - numeric identifiers always have lower precedence than non-numeric ones;
   - if all shared identifiers are equal, the longer set has higher precedence.

Official example chain (must hold):

```text
1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta
< 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0
```

`1.0.0+build.1` and `1.0.0+build.2` have equal precedence because build metadata
is ignored.

Source (fetched 2026-11-20): https://semver.org/spec/v2.0.0.html — section 11
"Precedence" and section 10 "Build metadata". Inputs are valid SemVer strings;
input validation is not required.
