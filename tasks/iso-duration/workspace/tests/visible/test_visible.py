# Visible cases avoid the month/minute ambiguity and the zero canonical form.
from src.iso_duration import format_duration, parse_duration


def test_simple_years() -> None:
    parsed = parse_duration("P3Y")
    assert parsed["years"] == 3
    assert parsed["seconds"] == 0


def test_full_duration() -> None:
    parsed = parse_duration("P3Y6M4DT12H30M5S")
    assert parsed["years"] == 3
    assert parsed["months"] == 6
    assert parsed["days"] == 4
    assert parsed["hours"] == 12
    assert parsed["minutes"] == 30
    assert parsed["seconds"] == 5


def test_format_roundtrip() -> None:
    assert format_duration(parse_duration("P3Y6M4DT12H30M5S")) == "P3Y6M4DT12H30M5S"


def test_negative_component_rejected() -> None:
    try:
        format_duration({"days": -1})
    except ValueError:
        return
    raise AssertionError("expected ValueError")
