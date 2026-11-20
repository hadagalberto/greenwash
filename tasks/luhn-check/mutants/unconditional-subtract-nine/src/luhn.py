"""Mutant: subtract 9 from every doubled digit, not only those above 9."""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def luhn_check_digit(payload: str) -> str:
    """Return the Luhn check digit for a non-empty digits-only ``payload``."""
    total = 0
    last = len(payload) - 1
    for index, char in enumerate(payload):
        digit = int(char)
        if (last - index) % 2 == 0:
            digit = digit * 2 - 9
        total += digit
    return str((10 - total % 10) % 10)


def is_valid(number: str) -> bool:
    """Return whether ``number`` has a correct final Luhn check digit."""
    if len(number) < 2 or not _ascii_digits(number):
        return False
    return luhn_check_digit(number[:-1]) == number[-1]
