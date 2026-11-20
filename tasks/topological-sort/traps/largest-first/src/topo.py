"""Plausible wrong solution: pick the largest available node first."""

from collections import defaultdict


def topological_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Return a topological ordering using largest-first tie-breaking."""
    known = set(nodes)
    for source, target in edges:
        if source not in known or target not in known:
            raise ValueError(f"edge ({source!r}, {target!r}) references an unknown node")
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node: 0 for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1
    ready = [node for node in nodes if indegree[node] == 0]
    order: list[str] = []
    while ready:
        node = max(ready)
        ready.remove(node)
        order.append(node)
        for neighbour in outgoing[node]:
            indegree[neighbour] -= 1
            if indegree[neighbour] == 0:
                ready.append(neighbour)
    if len(order) != len(nodes):
        raise ValueError("cycle detected")
    return order
