"""Trap: UPC-A check digit uses the EAN-13 weights (1, 3 instead of 3, 1)."""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def ean13_check_digit(payload12: str) -> str:
    """Return the EAN-13 check digit for a 12-digit ``payload12``."""
    total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(payload12))
    return str((10 - total % 10) % 10)


def is_valid_ean13(code: str) -> bool:
    """Return whether ``code`` is a 13-digit EAN-13 with a valid check digit."""
    if len(code) != 13 or not _ascii_digits(code):
        return False
    return ean13_check_digit(code[:12]) == code[12]


def upca_check_digit(payload11: str) -> str:
    """Return the UPC-A check digit for an 11-digit ``payload11``."""
    total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(payload11))
    return str((10 - total % 10) % 10)


def is_valid_upca(code: str) -> bool:
    """Return whether ``code`` is a 12-digit UPC-A with a valid check digit."""
    if len(code) != 12 or not _ascii_digits(code):
        return False
    return upca_check_digit(code[:11]) == code[11]
