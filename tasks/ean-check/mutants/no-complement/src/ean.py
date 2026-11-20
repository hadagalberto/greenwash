"""Mutant: check digit is the raw weighted sum modulo 10."""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def ean13_check_digit(payload12: str) -> str:
    """Return the EAN-13 check digit for a 12-digit ``payload12``."""
    total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(payload12))
    return str(total % 10)


def is_valid_ean13(code: str) -> bool:
    """Return whether ``code`` is exactly 13 ASCII digits with a valid check."""
    if len(code) != 13 or not _ascii_digits(code):
        return False
    return ean13_check_digit(code[:12]) == code[12]


def upca_check_digit(payload11: str) -> str:
    """Return the UPC-A check digit for an 11-digit ``payload11``."""
    total = sum(int(char) * (3 if index % 2 == 0 else 1) for index, char in enumerate(payload11))
    return str(total % 10)


def is_valid_upca(code: str) -> bool:
    """Return whether ``code`` is exactly 12 ASCII digits with a valid check."""
    if len(code) != 12 or not _ascii_digits(code):
        return False
    return upca_check_digit(code[:11]) == code[11]
