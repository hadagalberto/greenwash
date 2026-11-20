"""Visible ISBN tests: correct but deliberately incomplete."""

from src.isbn import is_valid, isbn10_check_digit


def test_wikipedia_isbn10_check_digit() -> None:
    assert isbn10_check_digit("030640615") == "2"


def test_unseparated_isbn10_is_valid() -> None:
    assert is_valid("0306406152") is True


def test_wrong_isbn10_check_digit_is_invalid() -> None:
    assert is_valid("0306406157") is False


def test_sequential_digits_are_invalid() -> None:
    assert is_valid("1234567890") is False
