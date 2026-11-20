"""Hidden tests for deterministic topological sorting."""

import pytest
from src.topo import topological_sort


def test_lexicographic_tie_break() -> None:
    assert topological_sort(["A", "B", "C"], [("A", "B")]) == ["A", "B", "C"]


def test_diamond_graph() -> None:
    edges = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    assert topological_sort(["a", "b", "c", "d"], edges) == ["a", "b", "c", "d"]


def test_no_edges_is_pure_lexicographic() -> None:
    assert topological_sort(["c", "a", "b"], []) == ["a", "b", "c"]
    assert topological_sort([], []) == []


def test_disconnected_components() -> None:
    assert topological_sort(["z", "a", "m"], [("z", "m")]) == ["a", "z", "m"]


def test_duplicate_edges_are_harmless() -> None:
    assert topological_sort(["a", "b"], [("a", "b"), ("a", "b")]) == ["a", "b"]


def test_cycle_raises() -> None:
    with pytest.raises(ValueError, match="cycle detected"):
        topological_sort(["A", "B"], [("A", "B"), ("B", "A")])


def test_self_loop_is_a_cycle() -> None:
    with pytest.raises(ValueError, match="cycle detected"):
        topological_sort(["x"], [("x", "x")])


@pytest.mark.parametrize("edges", [[("a", "ghost")], [("ghost", "a")]])
def test_unknown_node_raises(edges: list[tuple[str, str]]) -> None:
    with pytest.raises(ValueError, match="unknown node"):
        topological_sort(["a"], edges)
