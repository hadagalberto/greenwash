"""Hidden tests for half-open interval merging; expected values verified by hand."""

from src.intervals import merge


def test_touching_intervals_are_merged() -> None:
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]
    assert merge([(1, 2), (2, 3), (4, 5)]) == [(1, 3), (4, 5)]


def test_unsorted_input_is_sorted_by_start() -> None:
    assert merge([(5, 6), (1, 2), (3, 4)]) == [(1, 2), (3, 4), (5, 6)]


def test_negative_endpoints() -> None:
    assert merge([(-2, 1), (-3, -1)]) == [(-3, 1)]


def test_zero_length_intervals() -> None:
    assert merge([(1, 1)]) == [(1, 1)]
    assert merge([(1, 1), (1, 2)]) == [(1, 2)]
    assert merge([(1, 1), (3, 4)]) == [(1, 1), (3, 4)]
    assert merge([(1, 5), (2, 2)]) == [(1, 5)]


def test_contained_interval_does_not_survive() -> None:
    assert merge([(1, 2), (2, 100), (3, 4)]) == [(1, 100)]


def test_input_is_not_mutated() -> None:
    data = [(3, 5), (1, 2)]
    assert merge(data) == [(1, 2), (3, 5)]
    assert data == [(3, 5), (1, 2)]


def test_adjacent_chain_and_zero_length_boundary() -> None:
    assert merge([(0, 1), (1, 1), (2, 2), (2, 3)]) == [(0, 1), (2, 3)]
