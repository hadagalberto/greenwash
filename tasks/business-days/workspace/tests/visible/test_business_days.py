"""Visible tests: correct but deliberately incomplete."""

from src.business_days import add_business_days


def test_zero_days_returns_start_unchanged() -> None:
    assert add_business_days("2024-01-01", 0, ()) == "2024-01-01"


def test_zero_days_on_weekend_returns_start_unchanged() -> None:
    assert add_business_days("2024-01-06", 0, ()) == "2024-01-06"
    assert add_business_days("2024-01-07", 0, ()) == "2024-01-07"


def test_forward_from_weekend_skips_weekend() -> None:
    assert add_business_days("2024-01-06", 1, ()) == "2024-01-08"
    assert add_business_days("2024-01-07", 1, ()) == "2024-01-08"


def test_two_forward_days_from_sunday() -> None:
    assert add_business_days("2024-01-07", 2, ()) == "2024-01-09"
