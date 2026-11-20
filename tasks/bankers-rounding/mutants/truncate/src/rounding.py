"""Mutant: the round-up decision was deleted (digits are only truncated)."""

from __future__ import annotations


def round_half_even(value: str, places: int) -> str:
    """Return ``value`` rounded to exactly ``places`` fractional digits."""
    negative = value.startswith("-")
    magnitude = value[1:] if negative else value
    integer_part, _, fraction = magnitude.partition(".")

    digits = fraction + "0" * (places + 1 - len(fraction))
    kept = int((integer_part + digits[:places]) or "0")

    if places == 0:
        result = str(kept)
    else:
        scale = 10**places
        result = f"{kept // scale}.{kept % scale:0{places}d}"

    if negative and kept != 0:
        result = "-" + result
    return result
