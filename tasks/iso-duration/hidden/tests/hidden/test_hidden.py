# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: ## Supported grammar Only the designator form with **non-negative ...
#     -> test_format_rejects_non_integer_negative_and_bool_components,
#       test_zero_duration_representations_are_equivalent, test_canonical_format
# R2: - Date designators (`Y`, `M`, `W`, `D`) may appear only before `T`, ...
#     -> test_canonical_format, test_format_rejects_non_integer_negative_and_bool_components,
#       test_full_spec_format_example
# R3: - Time designators (`H`, `M`, `S`) may appear only after `T`, in ...
#     -> test_canonical_format, test_format_rejects_non_integer_negative_and_bool_components,
#       test_full_spec_format_example
# R4: - `T` may appear at most once and must be followed by at least one ...
#     -> test_canonical_format, test_format_rejects_non_integer_negative_and_bool_components,
#       test_full_spec_format_example
#
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


def test_full_spec_parse_example() -> None:
    # spec.md: parse_duration('P3Y6M4DT12H30M5S') sets all components as written.
    parsed = parse_duration("P3Y6M4DT12H30M5S")
    assert tuple(parsed[key] for key in KEYS) == (3, 6, 0, 4, 12, 30, 5)


def test_full_spec_format_example() -> None:
    # spec.md: format_duration({'years': 1, 'hours': 2}) == 'P1YT2H' and the
    # canonical form omits T when no time component is present.
    assert format_duration({"years": 1, "hours": 2}) == "P1YT2H"
    assert (
        format_duration(
            {"years": 3, "months": 6, "days": 4, "hours": 12, "minutes": 30, "seconds": 5}
        )
        == "P3Y6M4DT12H30M5S"
    )


def test_format_rejects_non_integer_negative_and_bool_components() -> None:
    # spec.md: every listed component must be a non-negative integer.
    for bad in ({"days": -1}, {"days": 1.5}, {"days": True}):
        with pytest.raises(ValueError):
            format_duration(bad)


def test_zero_duration_representations_are_equivalent() -> None:
    # spec.md / Wikipedia: PT0S and P0D represent the same zero duration.
    assert parse_duration("PT0S") == parse_duration("P0D")
    assert format_duration(parse_duration("PT0S")) == "P0D"
