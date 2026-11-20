# Visible documents have no inline comments, continuations or duplicate sections.
from src.ini_parse import parse_ini


def test_basic_sections() -> None:
    assert parse_ini("[a]\nx = 1\ny: 2\n") == {"a": {"x": "1", "y": "2"}}


def test_full_line_comments_and_blanks() -> None:
    text = "; heading\n\n[a]\n# note\nx = 1\n"
    assert parse_ini(text) == {"a": {"x": "1"}}


def test_quoted_value() -> None:
    assert parse_ini('[a]\nx = "hello"\n') == {"a": {"x": "hello"}}


def test_garbage_line_rejected() -> None:
    try:
        parse_ini("nonsense\n")
    except ValueError:
        return
    raise AssertionError("expected ValueError")
