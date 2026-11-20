"""Trap: doubling parity taken from the left for every payload length.

This matches the correct algorithm for even-length payloads, which is why it
passes the visible tests, but it is wrong for odd-length payloads.
"""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def luhn_check_digit(payload: str) -> str:
    """Return the check digit, doubling odd 0-based indices from the left."""
    total = 0
    for index, char in enumerate(payload):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return str((10 - total % 10) % 10)


def is_valid(number: str) -> bool:
    """Return whether ``number`` has a correct final Luhn check digit."""
    if len(number) < 2 or not _ascii_digits(number):
        return False
    return luhn_check_digit(number[:-1]) == number[-1]
