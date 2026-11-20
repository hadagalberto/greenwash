# Deterministic topological sort

Implement `src/topo.py` exporting:

```python
def topological_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]
```

A directed edge `(u, v)` means `u` must appear before `v` in the result. This is
the standard topological-ordering definition: for every edge `(u, v)`, `u`
precedes `v`. An ordering exists exactly when the graph is acyclic; see
"Topological sorting", Algorithms / Kahn's algorithm (fetched 2026-11-20):
https://en.wikipedia.org/wiki/Topological_sorting (Kahn, 1962; Cormen et al.,
*Introduction to Algorithms*, 2nd ed., section 22.4).

Requirements:

- Return every node from `nodes` exactly once, respecting all edges. The order
  is deterministic: repeatedly, among the nodes whose current in-degree is zero
  (all predecessors already emitted), emit the **lexicographically smallest**
  one. This is Kahn's algorithm with a min-heap / lexicographic tie-break.
- Duplicate edges are harmless: they must not change the result.
- If no ordering exists because the graph has a directed cycle, raise
  `ValueError("cycle detected")`. A self-loop is a cycle.
- If either endpoint of an edge is not in `nodes`, raise `ValueError` whose
  message contains the literal phrase `unknown node` and the name of the
  unknown endpoint (e.g. `ValueError("edge ('a', 'ghost') references an
  unknown node")`).

## Examples

- `topological_sort(["A", "B", "C"], [("A", "B")]) == ["A", "B", "C"]`.
  Initially `A` and `C` have in-degree zero and `A` is lexicographically
  smaller. After emitting `A`, both `B` and `C` are available; `B` is smaller
  than `C`, so `B` is emitted next, then `C`.
- `topological_sort(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
  == ["a", "b", "c", "d"]`.
- `topological_sort(["c", "a", "b"], []) == ["a", "b", "c"]` (no edges: pure
  lexicographic order).
- `topological_sort(["x"], []) == ["x"]`; `topological_sort([], []) == []`.
- `topological_sort(["A", "B"], [("A", "B"), ("B", "A")])` raises
  `ValueError("cycle detected")`.
- `topological_sort(["a", "b"], [("a", "b"), ("a", "b")]) == ["a", "b"]`
  (duplicate edges).
- `topological_sort(["a"], [("a", "ghost")])` raises `ValueError` whose message
  contains `unknown node` and `ghost`.
