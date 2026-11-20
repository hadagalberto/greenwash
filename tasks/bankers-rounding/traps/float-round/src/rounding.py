"""Trap: converts to binary float and uses Python's built-in round()."""

from __future__ import annotations


def round_half_even(value: str, places: int) -> str:
    """Return ``value`` rounded to exactly ``places`` fractional digits."""
    return f"{round(float(value), places):.{places}f}"
