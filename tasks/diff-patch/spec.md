# Unified diff patch application

Implement two modules: `src/hunk.py` and `src/patch.py`.

## `src/hunk.py`

`parse_hunk_header(header: str) -> HunkRange`, where `HunkRange` is a frozen
dataclass with `old_start, old_count, new_start, new_count` (all `int`).

Header format: `@@ -<start>[,<count>] +<start>[,<count>] @@` with an optional
trailing ` <context text>`. A missing `,count` means `1`. Starts must be `>= 1`,
counts `>= 0`. Anything else raises `ValueError`.

## `src/patch.py`

`apply_patch(lines: Sequence[str], patch: Sequence[str]) -> list[str]`.

- `lines` are logical lines **without** trailing newline characters.
- Lines in `patch` before the first `@@` (e.g. `--- a`, `+++ b`) are ignored.
- After a header, body lines start with `' '` (context), `'-'` (removed) or
  `'+'` (added). A line `\ No newline at end of file` is ignored anywhere in
  a hunk. The hunk ends at the next `@@` or at any other non-body line.
- Context and removed lines form the *old* sequence; context and added lines
  form the *new* sequence. Their lengths must equal `old_count` and
  `new_count` from the header, or `ValueError` is raised.
- `old_start` is **1-based** in the current document. The old sequence at that
  position must match exactly, or `ValueError` is raised. Replace it with the
  new sequence, then continue with the next hunk (positions refer to the
  document as modified by earlier hunks).
- Hunks outside the document raise `ValueError`.

## Examples

```
apply_patch(['a', 'b', 'c'],
            ['@@ -1,2 +1,2 @@', '-a', '-b', '+x', '+y']) == ['x', 'y', 'c']

apply_patch(['a','b','c','d'],
            ['--- old','+++ new',
             '@@ -2,3 +2,4 @@', ' b', '-c', '+C', '+X', ' d'])
  == ['a','b','C','X','d']
```

## Source (fetched 2026-11-20)

GNU diffutils manual, "Unified Format": a hunk begins with
`@@ -l,s +l,s @@ optional section heading`; lines beginning with `-`, `+` or a
space are removals, additions and context respectively:
https://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html
