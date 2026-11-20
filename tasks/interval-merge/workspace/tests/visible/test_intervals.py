"""Visible tests: correct but deliberately incomplete."""

from src.intervals import merge


def test_empty_input() -> None:
    assert merge([]) == []


def test_strictly_overlapping_pair() -> None:
    assert merge([(1, 3), (2, 4)]) == [(1, 4)]


def test_containment() -> None:
    assert merge([(1, 4), (1, 3)]) == [(1, 4)]


def test_overlap_with_negative_endpoints() -> None:
    assert merge([(-2, 1), (0, 3)]) == [(-2, 3)]
