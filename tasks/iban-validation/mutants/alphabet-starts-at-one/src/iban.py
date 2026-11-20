"""Mutant: letter expansion offset changed from 55 to 64 (A=1 instead of A=10)."""

from __future__ import annotations

_COUNTRY_LENGTHS = {"GB": 22, "DE": 22, "IE": 22, "FR": 27, "ES": 24, "NL": 18, "BE": 16}


def _normalize(iban: str) -> str:
    return iban.replace(" ", "").upper()


def mod97(iban: str) -> int:
    value = _normalize(iban)
    rearranged = value[4:] + value[:4]
    expanded = "".join(str(ord(ch) - 64) if ch.isalpha() else ch for ch in rearranged)
    return int(expanded) % 97


def is_valid(iban: str) -> bool:
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
