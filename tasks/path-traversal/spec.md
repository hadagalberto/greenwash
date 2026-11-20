# Safely join an untrusted path to a base directory

Implement `src/path.ts` exporting exactly:

```ts
export function safeJoin(base: string, userPath: string): string | null
```

This is pure string logic: **do not use `node:fs`** and do not touch the
filesystem. Return a normalized absolute-style path using `/` as the only output
separator, or `null` when the input is rejected.

## Path style used by this task

`base` is an absolute POSIX-style directory path, e.g. `/srv/data`. Example:
`safeJoin("/srv/data", "file.txt") === "/srv/data/file.txt"`. Both `/` and `\`
are accepted as **input** separators in either argument; output always uses `/`.
Duplicate separators and `.` segments are removed. A `..` segment in `base`
pops the previous base segment (clamped at the root).

## Rejection rules (return `null`)

1. `userPath` is the empty string (`""`). Whitespace-only paths are not empty;
   they are ordinary segment names.
2. `userPath` starts with `/` or `\` (absolute path), or matches
   `/^[A-Za-z]:/` (Windows drive-letter path). Case does not matter for the
   letter.
3. Either `base` or `userPath` contains a NUL character (`\u0000`).
4. Any `..` segment in `userPath` that would climb above `base`: after
   normalizing, if a `..` appears when no previously-seen non-`.`, non-`..`
   segment of `userPath` remains to cancel it, reject. A `..` that merely
   cancels an earlier user segment is allowed.

Everything else is a normal segment and is kept verbatim (including spaces,
`...`, and percent signs — no decoding is performed).

## Algorithm summary

Split `base` and `userPath` on runs of `/` or `\`, discarding empty pieces.
Build the result from the normalized base segments, then process user segments
left to right: `.` is ignored; a normal segment is pushed; `..` pops one pushed
user segment, or returns `null` if none is available. Render as
`"/" + segments.join("/")` (so a single root segment list renders as `/`).

## Examples (exact expectations, base `/srv/data`)

| `userPath` | result |
| --- | --- |
| `"file.txt"` | `"/srv/data/file.txt"` |
| `"a/b.txt"` | `"/srv/data/a/b.txt"` |
| `"a//b///c"` | `"/srv/data/a/b/c"` |
| `"a\\.\\b"` | `"/srv/data/a/b"` |
| `"a/../b"` | `"/srv/data/b"` |
| `"."` | `"/srv/data"` |
| `""` | `null` |
| `"../secret"` | `null` |
| `"a/../../secret"` | `null` |
| `"a\\..\\..\\b"` | `null` |
| `"/etc/passwd"` | `null` |
| `"\\etc\\passwd"` | `null` |
| `"C:\\secret"` | `null` |
| `"a\u0000b"` | `null` |
| `"..."` | `"/srv/data/..."` |

Also: `safeJoin("/srv//data/", "f") === "/srv/data/f"` and
`safeJoin("/", "f") === "/f"`.

## Sources (fetched 2026-11-20)

- https://www.rfc-editor.org/rfc/rfc3986.txt — Section 5.2.4 "Remove Dot
  Segments" defines the normalization of `.` and `..` path segments; Section 7.2
  "Malicious Construction" notes that relative references can be used to
  construct URIs that point outside an intended hierarchy.
- https://owasp.org/www-community/attacks/Path_Traversal — dot-dot-slash and
  absolute-path traversal, backslash separators on Windows, extra `. \ /`
  characters, and NUL-byte truncation are all listed as attack variations; the
  recommended defense is to validate input by accepting only known-good paths
  and to normalize before use.
