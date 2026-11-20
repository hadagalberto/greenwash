"""Visible tests: correct but deliberately incomplete."""

from src.topo import topological_sort


def test_forced_chain() -> None:
    assert topological_sort(["a", "b", "c"], [("a", "b"), ("b", "c")]) == ["a", "b", "c"]


def test_single_node_no_edges() -> None:
    assert topological_sort(["x"], []) == ["x"]
