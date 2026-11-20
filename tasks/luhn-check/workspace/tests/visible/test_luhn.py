"""Visible Luhn tests: correct but deliberately incomplete."""

from src.luhn import is_valid, luhn_check_digit


def test_wikipedia_check_digit() -> None:
    assert luhn_check_digit("1789372997") == "4"


def test_wikipedia_number_is_valid() -> None:
    assert is_valid("17893729974") is True


def test_wikipedia_number_with_wrong_check_digit_is_invalid() -> None:
    assert is_valid("17893729975") is False


def test_other_wrong_check_digit_is_invalid() -> None:
    assert is_valid("79927398710") is False
