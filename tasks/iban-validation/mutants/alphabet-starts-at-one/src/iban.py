"""IBAN validation (ISO 13616) with ISO/IEC 7064 MOD-97-10 check digits."""

from __future__ import annotations

_COUNTRY_LENGTHS = {"GB": 22, "DE": 22, "IE": 22, "FR": 27, "ES": 24, "NL": 18, "BE": 16}


def _normalize(iban: str) -> str:
    """Strip grouping spaces and upper-case letters."""
    return iban.replace(" ", "").upper()


def mod97(iban: str) -> int:
    """Return the MOD-97-10 remainder of a normalized, expanded IBAN."""
    value = _normalize(iban)
    rearranged = value[4:] + value[:4]
    expanded = "".join(str(ord(ch) - 56) if ch.isalpha() else ch for ch in rearranged)
    return int(expanded) % 97


def is_valid(iban: str) -> bool:
    """Return True only for a well-formed, supported, check-digit-valid IBAN."""
    value = _normalize(iban)
    if len(value) < 4:
        return False
    country = value[:2]
    if country not in _COUNTRY_LENGTHS:
        return False
    if len(value) != _COUNTRY_LENGTHS[country]:
        return False
    if not value[:2].isalpha() or not value[2:4].isdigit():
        return False
    if not value.isascii() or not value.isalnum():
        return False
    return mod97(value) == 1
