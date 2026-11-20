# Hand-chosen Unicode vectors; expected values follow NFC/NFD + casefold rules.
import pytest
from src.unicode_text import canonical_key, normalized_equal, strip_marks


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("é", "e\u0301"),
        ("É", "E\u0301"),
        ("Straße", "STRASSE"),
        ("Å", "Å"),
        ("K", "k"),
        ("ABC", "abc"),
        ("ﬁ", "fi"),
    ],
)
def test_normalized_equal_accepts_equivalent_pairs(left: str, right: str) -> None:
    assert normalized_equal(left, right) is True


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("é", "e"),
        ("Straße", "Strasse "),
        ("abc", "ABCd"),
    ],
)
def test_normalized_equal_rejects_different_pairs(left: str, right: str) -> None:
    assert normalized_equal(left, right) is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Café", "Cafe"),
        ("e\u0301x", "ex"),
        ("Ångström", "Angstrom"),
        ("naïve", "naive"),
        ("abc", "abc"),
    ],
)
def test_strip_marks(text: str, expected: str) -> None:
    assert strip_marks(text) == expected


def test_canonical_key_re_normalizes_after_casefold() -> None:
    assert canonical_key("İ") == "i\u0307"
    assert canonical_key("ΐ") == "ΐ"


def test_strip_marks_type_error() -> None:
    with pytest.raises(TypeError):
        strip_marks(5)  # type: ignore[arg-type]
