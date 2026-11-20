# ISO 8601 durations (integer subset)

Implement `parse_duration` and `format_duration` in `src/iso_duration.py`.

## Supported grammar

Only the designator form with **non-negative integer** values is supported:

```
P[nY][nM][nW][nD][T[nH][nM][nS]]
```

- `P` is mandatory and at least one component designator must be present
  (an explicitly written zero such as `PT0S` is valid).
- Date designators (`Y`, `M`, `W`, `D`) may appear only before `T`, in that
  strict order, each at most once.
- Time designators (`H`, `M`, `S`) may appear only after `T`, in that strict
  order, each at most once.
- `T` may appear at most once and must be followed by at least one time
  component. No fraction, no sign, no basic `PYYYYMMDDThhmmss` form.
- `M` before `T` means months; `M` after `T` means minutes.

`parse_duration(text)` returns a `dict` with exactly the keys `years, months,
weeks, days, hours, minutes, seconds` and integer values (missing components
are `0`). Invalid input raises `ValueError`.

`format_duration(components)` accepts a mapping, validates that every listed
component is a non-negative integer (missing keys mean `0`), and returns the
canonical string: omit zero components; omit `T` when all time components are
zero; return `'P0D'` when everything is zero.

## Examples

```
parse_duration('P3Y')            -> years=3
parse_duration('P1M')            -> months=1
parse_duration('PT1M')           -> minutes=1
parse_duration('P3Y6M4DT12H30M5S') -> all set as written
parse_duration('P1W2D')          -> weeks=1, days=2
parse_duration('PT0S')           -> all zero  (valid input)
parse_duration('P')              -> ValueError
parse_duration('P1MT')           -> ValueError
parse_duration('P1D2Y')          -> ValueError  (wrong order)
parse_duration('P1M2M')          -> ValueError  (duplicate)

format_duration({'years': 1, 'hours': 2}) -> 'P1YT2H'
format_duration({'seconds': 0})           -> 'P0D'
```

## Source (fetched 2026-11-20)

Wikipedia, "ISO 8601", section "Durations": `PnYnMnDTnHnMnS` and `PnW`;
"P1M is a one-month duration and PT1M is a one-minute duration";
"`PT0S` or `P0D` ... represent the same duration":
https://en.wikipedia.org/wiki/ISO_8601#Durations
