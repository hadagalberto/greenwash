# Merge half-open integer intervals

Implement `src/intervals.py` exporting:

```python
def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]
```

Each input pair `(a, b)` denotes the half-open interval `[a, b)` — all values
`x` with `a <= x < b`. Input is assumed valid: `a <= b`. See "Interval
(mathematics)", Half-open intervals (fetched 2026-11-20):
https://en.wikipedia.org/wiki/Interval_(mathematics).

Return the union of the input intervals as a list of `(start, end)` pairs with:

- results sorted by increasing `start`;
- overlapping **or touching** intervals merged — for `a <= c`, the intervals
  `[a, b)` and `[c, d)` are merged whenever `c <= b`, so `[1, 3)` and `[3, 5)`
  become `[1, 5)` (adjacency counts);
- zero-length intervals `[a, a)` preserved when not contained in a merged
  interval (`[1, 1)` alone stays `[1, 1)`; `[1, 1)` with `[1, 2)` becomes
  `[1, 2)`);
- empty input returns `[]`;
- the input list must not be modified.

## Examples

- `merge([(1, 3), (2, 4)]) == [(1, 4)]` (overlap).
- `merge([(1, 3), (3, 5)]) == [(1, 5)]` (touching endpoints).
- `merge([(1, 2), (2, 3), (4, 5)]) == [(1, 3), (4, 5)]`.
- `merge([(5, 6), (1, 2), (3, 4)]) == [(1, 2), (3, 4), (5, 6)]` (unsorted input).
- `merge([(-2, 1), (-3, -1)]) == [(-3, 1)]` (negative endpoints).
- `merge([(1, 4), (2, 3)]) == [(1, 4)]` (containment).
- `merge([(1, 2), (2, 100), (3, 4)]) == [(1, 100)]` (a contained interval must
  not survive as a separate result).
- `merge([(1, 1)]) == [(1, 1)]`; `merge([(1, 1), (1, 2)]) == [(1, 2)]`;
  `merge([]) == []`.
