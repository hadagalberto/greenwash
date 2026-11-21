# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: A **business day** is a date that is Monday through Friday and is ...
#     -> test_many_holidays_skip_to_next_business_day, test_forward_from_business_day,
#       test_weekend_is_not_a_business_day
# R2: Holiday strings are exact dates only: no observance shifting (a ...
#     -> test_weekend_holiday_is_not_shifted_to_monday,
#       test_negative_with_holiday_spanning_weekend,
#       test_zero_days_ignores_weekend_and_holiday_status
# R3: Semantics: - `days > 0`: count business days strictly **after** ...
#     -> test_negative_counts_strictly_before_start, test_forward_from_business_day,
#       test_many_holidays_skip_to_next_business_day
# R4: - `days < 0`: count business days strictly **before** `start`; ...
#     -> test_negative_counts_strictly_before_start, test_forward_from_business_day,
#       test_many_holidays_skip_to_next_business_day
#
"""Hidden tests for business-day arithmetic; expected values verified by hand."""

from src.business_days import add_business_days


def test_forward_from_business_day() -> None:
    assert add_business_days("2024-01-01", 1, ()) == "2024-01-02"
    assert add_business_days("2024-02-26", 3, ()) == "2024-02-29"


def test_negative_counts_strictly_before_start() -> None:
    assert add_business_days("2024-01-01", -1, ()) == "2023-12-29"
    assert add_business_days("2024-01-03", -3, ()) == "2023-12-29"
    assert add_business_days("2024-01-09", -2, ()) == "2024-01-05"


def test_weekend_is_not_a_business_day() -> None:
    assert add_business_days("2024-01-05", 1, ()) == "2024-01-08"
    assert add_business_days("2024-01-04", 2, ()) == "2024-01-08"


def test_holidays_are_excluded() -> None:
    assert add_business_days("2024-01-05", 1, ("2024-01-08",)) == "2024-01-09"
    assert add_business_days("2024-01-01", 5, ("2024-01-02",)) == "2024-01-09"


def test_negative_with_holiday_spanning_weekend() -> None:
    assert add_business_days("2024-01-08", -1, ("2024-01-05",)) == "2024-01-04"
    assert add_business_days("2024-01-01", -5, ("2023-12-29",)) == "2023-12-22"


def test_zero_days_ignores_weekend_and_holiday_status() -> None:
    assert add_business_days("2024-01-06", 0, ("2024-01-06",)) == "2024-01-06"
    assert add_business_days("2024-01-01", 0, ("2024-01-01",)) == "2024-01-01"


def test_many_holidays_skip_to_next_business_day() -> None:
    excluded = ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08")
    assert add_business_days("2024-01-01", 1, excluded) == "2024-01-09"


def test_weekend_holiday_is_not_shifted_to_monday() -> None:
    # spec.md: a holiday falling on a Saturday is NOT moved to the following
    # Monday. 2024-01-06 is a Saturday, so it cannot exclude Monday 01-08.
    assert add_business_days("2024-01-05", 1, ("2024-01-06",)) == "2024-01-08"
