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


def test_spec_examples() -> None:
    # Every expectation is listed verbatim in the spec.md Examples block.
    assert canonical_key("ABC") == "abc"
    assert normalized_equal("é", "e\u0301") is True
    assert normalized_equal("Straße", "STRASSE") is True
    assert normalized_equal("Å", "Å") is True
    assert canonical_key("K") == "k"
    assert strip_marks("Café") == "Cafe"
    assert strip_marks("e\u0301x") == "ex"
    assert strip_marks("abc") == "abc"


def test_canonical_key_and_normalized_equal_type_errors() -> None:
    # spec.md: canonical_key rejects non-strings; normalized_equal delegates to it.
    with pytest.raises(TypeError):
        canonical_key(5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        normalized_equal(5, "abc")  # type: ignore[arg-type]


def test_strip_marks_preserves_case_and_applies_no_transliteration() -> None:
    # spec.md: only marks are dropped; case and non-decomposable letters remain.
    assert strip_marks("É") == "E"
    assert strip_marks("Straße") == "Straße"
