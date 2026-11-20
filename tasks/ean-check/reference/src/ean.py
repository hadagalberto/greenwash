"""EAN-13 and UPC-A check digits and validation.

Sources: https://en.wikipedia.org/wiki/International_Article_Number
and https://www.gs1.org/standards/checkdigits
"""

from __future__ import annotations


def _ascii_digits(text: str) -> bool:
    return bool(text) and all("0" <= char <= "9" for char in text)


def ean13_check_digit(payload12: str) -> str:
    """Return the EAN-13 check digit for a 12-digit ``payload12``.

    Weights alternate 1, 3 from the left; check = (10 - total % 10) % 10.
    """
    total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(payload12))
    return str((10 - total % 10) % 10)


def is_valid_ean13(code: str) -> bool:
    """Return whether ``code`` is exactly 13 ASCII digits with a valid check."""
    if len(code) != 13 or not _ascii_digits(code):
        return False
    return ean13_check_digit(code[:12]) == code[12]


def upca_check_digit(payload11: str) -> str:
    """Return the UPC-A check digit for an 11-digit ``payload11``.

    Weights alternate 3, 1 from the left; check = (10 - total % 10) % 10.
    """
    total = sum(int(char) * (3 if index % 2 == 0 else 1) for index, char in enumerate(payload11))
    return str((10 - total % 10) % 10)


def is_valid_upca(code: str) -> bool:
    """Return whether ``code`` is exactly 12 ASCII digits with a valid check."""
    if len(code) != 12 or not _ascii_digits(code):
        return False
    return upca_check_digit(code[:11]) == code[11]
