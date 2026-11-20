"""Mutant: ISBN-13 weights start at 3 instead of 1."""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def isbn10_check_digit(payload9: str) -> str:
    """Return the ISBN-10 check character for a 9-digit ``payload9``."""
    total = sum(int(char) * (10 - index) for index, char in enumerate(payload9))
    value = (11 - total % 11) % 11
    return "X" if value == 10 else str(value)


def isbn13_check_digit(payload12: str) -> str:
    """Return the ISBN-13 check digit for a 12-digit ``payload12``."""
    total = sum(int(char) * (3 if index % 2 == 0 else 1) for index, char in enumerate(payload12))
    return str((10 - total % 10) % 10)


def is_valid(isbn: str) -> bool:
    """Return whether ``isbn`` is a well-formed ISBN with a correct check."""
    cleaned = isbn.replace("-", "").replace(" ", "")
    if len(cleaned) == 10:
        if not _ascii_digits(cleaned[:9]) or cleaned[9] not in "0123456789X":
            return False
        return isbn10_check_digit(cleaned[:9]) == cleaned[9]
    if len(cleaned) == 13:
        if not _ascii_digits(cleaned):
            return False
        return isbn13_check_digit(cleaned[:12]) == cleaned[12]
    return False
