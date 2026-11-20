"""Deterministic topological sort (incomplete starting point)."""


def topological_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Return a topological ordering, breaking ties lexicographically."""
    if not edges:
        return sorted(nodes)
    return list(nodes)
