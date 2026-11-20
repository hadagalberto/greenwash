"""Visible IBAN tests: correct but deliberately incomplete."""

from src.iban import is_valid, mod97


def test_unknown_country_is_rejected() -> None:
    assert is_valid("ZZ82 1234 5678") is False


def test_too_short_iban_is_rejected() -> None:
    assert is_valid("GB82 WEST 1234 5698 7654 3") is False


def test_wrong_check_digits_are_rejected() -> None:
    assert is_valid("GB83 WEST 1234 5698 7654 32") is False


def test_nondigit_check_digits_are_rejected() -> None:
    assert is_valid("GBAA WEST 1234 5698 7654 32") is False


def test_non_alphanumeric_character_is_rejected() -> None:
    assert is_valid("GB82 WEST 1234 5698 7654 3!") is False


def test_mod97_returns_an_integer_remainder() -> None:
    for iban in ("GB82 WEST 1234 5698 7654 32", "GB83 WEST 1234 5698 7654 32"):
        remainder = mod97(iban)
        assert isinstance(remainder, int)
        assert 0 <= remainder < 97
