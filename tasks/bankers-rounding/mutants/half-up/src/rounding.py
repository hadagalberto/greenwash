"""Exact round-half-to-even on decimal strings (no binary floats)."""

from __future__ import annotations


def round_half_even(value: str, places: int) -> str:
    """Return ``value`` rounded to exactly ``places`` fractional digits."""
    negative = value.startswith("-")
    magnitude = value[1:] if negative else value
    integer_part, _, fraction = magnitude.partition(".")

    # One extra digit is needed beyond the kept places for the round decision;
    # any further digits form the sticky (above-halfway) information.
    digits = fraction + "0" * (places + 1 - len(fraction))
    kept = int((integer_part + digits[:places]) or "0")
    first_discarded = digits[places]
    _sticky = any(digit != "0" for digit in digits[places + 1 :])

    round_up = first_discarded > "5" or (first_discarded == "5" and kept % 2 == 1)
    if round_up:
        kept += 1

    if places == 0:
        result = str(kept)
    else:
        scale = 10**places
        result = f"{kept // scale}.{kept % scale:0{places}d}"

    if negative and kept != 0:
        result = "-" + result
    return result
