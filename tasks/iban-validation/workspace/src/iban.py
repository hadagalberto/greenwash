"""IBAN validation - incomplete starting point; implement the rules in spec.md."""

_COUNTRY_LENGTHS = {"GB": 22, "DE": 22, "IE": 22, "FR": 27, "ES": 24, "NL": 18, "BE": 16}


def mod97(iban: str) -> int:
    """Return the MOD-97-10 remainder (this stub is not the real algorithm)."""
    return 0


def is_valid(iban: str) -> bool:
    """Return True for a well-formed IBAN with valid check digits."""
    return False
