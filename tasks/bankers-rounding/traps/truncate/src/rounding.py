"""Trap: truncates the decimal digits instead of rounding them."""

from __future__ import annotations


def round_half_even(value: str, places: int) -> str:
    """Return ``value`` rounded to exactly ``places`` fractional digits."""
    negative = value.startswith("-")
    magnitude = value[1:] if negative else value
    integer_part, _, fraction = magnitude.partition(".")
    digits = (fraction + "0" * places)[:places]

    result = integer_part if places == 0 else f"{integer_part}.{digits}"
    if negative:
        result = "-" + result
    return result
