"""Trap: ``is_valid`` silently removes spaces and hyphens before checking."""

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
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return str((10 - total % 10) % 10)


def is_valid(number: str) -> bool:
    """Return whether ``number`` has a correct final Luhn check digit."""
    cleaned = number.replace(" ", "").replace("-", "")
    if len(cleaned) < 2 or not _ascii_digits(cleaned):
        return False
    return luhn_check_digit(cleaned[:-1]) == cleaned[-1]
