"""Luhn check digits and validation.

Algorithm: https://en.wikipedia.org/wiki/Luhn_algorithm
Specified in ISO/IEC 7812-1 Annex B: https://www.iso.org/standard/70484.html
"""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def luhn_check_digit(payload: str) -> str:
    """Return the Luhn check digit for a non-empty digits-only ``payload``.

    Numbering payload positions from the right starting at 1, digits in odd
    positions are doubled and reduced by 9 when the doubled value exceeds 9.
    """
    total = 0
    last = len(payload) - 1
    for index, char in enumerate(payload):
        digit = int(char)
        if (last - index) % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return str((10 - total % 10) % 10)


def is_valid(number: str) -> bool:
    """Return whether ``number`` is digit-only, at least two chars long and has
    a correct final Luhn check digit."""
    if len(number) < 2 or not _ascii_digits(number):
        return False
    return luhn_check_digit(number[:-1]) == number[-1]
