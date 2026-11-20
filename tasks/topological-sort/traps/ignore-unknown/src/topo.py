"""Plausible wrong solution: silently drops edges with unknown endpoints."""

import heapq
from collections import defaultdict


def topological_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    """Return a topological ordering, breaking ties lexicographically."""
    known = set(nodes)
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node: 0 for node in nodes}
    for source, target in edges:
        if source not in known or target not in known:
            continue
        outgoing[source].append(target)
        indegree[target] += 1
    ready = [node for node in nodes if indegree[node] == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for neighbour in outgoing[node]:
            indegree[neighbour] -= 1
            if indegree[neighbour] == 0:
                heapq.heappush(ready, neighbour)
    if len(order) != len(nodes):
        raise ValueError("cycle detected")
    return order
