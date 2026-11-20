"""Visible rational tests: correct but deliberately incomplete.

All operands here have positive denominators and each raw result is already in
lowest terms, so these tests do not exercise sign normalization or reduction.
"""

from src.rational import add, compare, div, mul, sub


def test_add_with_positive_denominators() -> None:
    assert add((1, 2), (1, 3)) == (5, 6)


def test_subtract_with_positive_denominators() -> None:
    assert sub((1, 3), (1, 5)) == (2, 15)


def test_multiply_with_positive_denominators() -> None:
    assert mul((2, 3), (5, 7)) == (10, 21)


def test_divide_with_positive_denominators() -> None:
    assert div((2, 3), (5, 7)) == (14, 15)


def test_compare_with_positive_denominators() -> None:
    assert compare((1, 2), (2, 3)) == -1
    assert compare((3, 4), (2, 3)) == 1
    assert compare((1, 2), (3, 6)) == 0
