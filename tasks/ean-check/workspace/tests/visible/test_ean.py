"""Visible EAN/UPC tests: correct but deliberately incomplete."""

from src.ean import is_valid_ean13, is_valid_upca


def test_ean13_wikipedia_example_is_valid() -> None:
    assert is_valid_ean13("5901234123457") is True


def test_ean13_stabilo_example_is_valid() -> None:
    assert is_valid_ean13("4006381333931") is True


def test_ean13_wrong_check_digit_is_invalid() -> None:
    assert is_valid_ean13("5901234123456") is False


def test_upca_wrong_check_digit_is_invalid() -> None:
    assert is_valid_upca("036000291453") is False
