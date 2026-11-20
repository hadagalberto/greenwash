"""Hidden round-half-to-even vectors.

Expected strings are worked out by hand from the exact decimal digits using
the tie rule in https://en.wikipedia.org/wiki/Rounding#Round_half_to_even and
https://docs.python.org/3/library/decimal.html#rounding-modes (ROUND_HALF_EVEN),
both fetched 2026-11-20. The 2.675 case is the decimal-vs-binary example from
the Python documentation. No expected value is computed by graded code.
"""

import pytest
from src.rounding import round_half_even

VECTORS = (
    ("2.5", 0, "2"),
    ("3.5", 0, "4"),
    ("1.25", 1, "1.2"),
    ("1.35", 1, "1.4"),
    ("0.5", 0, "0"),
    ("-2.5", 0, "-2"),
    ("-3.5", 0, "-4"),
    ("2.675", 2, "2.68"),
    ("1.005", 2, "1.00"),
    ("123.456", 1, "123.5"),
    ("0", 3, "0.000"),
    ("2", 0, "2"),
    ("1", 2, "1.00"),
)


@pytest.mark.parametrize(("value", "places", "expected"), VECTORS)
def test_official_rounding_vectors(value: str, places: int, expected: str) -> None:
    assert round_half_even(value, places) == expected


def test_tie_on_even_kept_digit_stays_down() -> None:
    assert round_half_even("4.5", 0) == "4"
    assert round_half_even("2.45", 1) == "2.4"


def test_tie_on_odd_kept_digit_goes_up() -> None:
    assert round_half_even("5.5", 0) == "6"
    assert round_half_even("2.35", 1) == "2.4"


def test_sticky_digit_forces_round_up_at_a_half() -> None:
    # Kept last digit is even (6), but a discarded 5 followed by 1 is above
    # the halfway point, so the result must round up to 2.47.
    assert round_half_even("2.4651", 2) == "2.47"


def test_negative_magnitude_tie_uses_even_digit() -> None:
    assert round_half_even("-1.25", 1) == "-1.2"
    assert round_half_even("-1.35", 1) == "-1.4"


def test_carry_propagates_through_nines() -> None:
    assert round_half_even("9.999", 1) == "10.0"
