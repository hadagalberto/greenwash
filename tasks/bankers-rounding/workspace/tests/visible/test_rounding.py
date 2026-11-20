"""Visible rounding tests: correct but deliberately incomplete.

These vectors do not contain a rounding tie, so they do not distinguish
banker's rounding from half-up, float-based rounding or truncation.
"""

from src.rounding import round_half_even


def test_integer_zero_places() -> None:
    assert round_half_even("2", 0) == "2"


def test_padding_an_integer() -> None:
    assert round_half_even("1", 2) == "1.00"


def test_zero_with_padding() -> None:
    assert round_half_even("0", 3) == "0.000"


def test_trailing_zeros_need_no_rounding() -> None:
    assert round_half_even("2.500", 2) == "2.50"


def test_negative_integer_keeps_its_sign() -> None:
    assert round_half_even("-7.000", 0) == "-7"


def test_negative_non_tie_rounds_down_in_magnitude() -> None:
    assert round_half_even("-1.234", 2) == "-1.23"
