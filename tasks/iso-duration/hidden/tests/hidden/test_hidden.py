# Hand-written vectors from the ISO 8601 rule cited in spec.md.
import pytest
from src.iso_duration import format_duration, parse_duration

KEYS = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("P1Y", (1, 0, 0, 0, 0, 0, 0)),
        ("P1M", (0, 1, 0, 0, 0, 0, 0)),
        ("PT1M", (0, 0, 0, 0, 0, 1, 0)),
        ("P1W2D", (0, 0, 1, 2, 0, 0, 0)),
        ("P23DT23H", (0, 0, 0, 23, 23, 0, 0)),
        ("P4Y", (4, 0, 0, 0, 0, 0, 0)),
        ("PT0S", (0, 0, 0, 0, 0, 0, 0)),
        ("P0D", (0, 0, 0, 0, 0, 0, 0)),
        ("PT36H", (0, 0, 0, 0, 36, 0, 0)),
    ],
)
def test_parse_vectors(text: str, expected: tuple[int, ...]) -> None:
    parsed = parse_duration(text)
    assert tuple(parsed[key] for key in KEYS) == expected


@pytest.mark.parametrize(
    "bad",
    [
        "P",
        "P1MT",
        "PT",
        "P1D2Y",
        "P1M2M",
        "PT1S2H",
        "P-1D",
        "P1.5D",
        "P1Y2W3M",
        "PT1M2M",
        "1Y",
        "PXY",
        "P1YT",
        "P1YTT2H",
    ],
)
def test_invalid_durations(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_duration(bad)


@pytest.mark.parametrize(
    ("components", "expected"),
    [
        ({"years": 1, "hours": 2}, "P1YT2H"),
        ({"weeks": 2, "seconds": 3}, "P2WT3S"),
        ({"seconds": 0}, "P0D"),
        ({}, "P0D"),
        ({"months": 6, "days": 4, "minutes": 5}, "P6M4DT5M"),
    ],
)
def test_canonical_format(components: dict[str, int], expected: str) -> None:
    assert format_duration(components) == expected


def test_parse_format_roundtrip_vectors() -> None:
    for text in ("P1M", "PT1M", "P1W2D", "P23DT23H"):
        assert format_duration(parse_duration(text)) == text
    assert format_duration(parse_duration("PT0S")) == "P0D"
