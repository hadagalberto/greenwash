# Visible vectors are ASCII-only: all reasonable implementations agree.
from src.unicode_text import canonical_key, normalized_equal, strip_marks


def test_ascii_casefold() -> None:
    assert canonical_key("abc") == "abc"
    assert normalized_equal("hello", "hello")


def test_ascii_inequality() -> None:
    assert normalized_equal("abc", "abd") is False


def test_strip_marks_ascii_is_identity() -> None:
    assert strip_marks("plain") == "plain"


def test_non_string_rejected() -> None:
    try:
        canonical_key(7)  # type: ignore[arg-type]
    except TypeError:
        return
    raise AssertionError("expected TypeError")
