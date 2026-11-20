# Expected dictionaries are written by hand from the documented rules.
import pytest
from src.ini_parse import parse_ini


def test_inline_comments_and_quotes() -> None:
    text = '[a]\nx = 1 ; note\ny: "two words" # note\nz = "a;b"\n'
    assert parse_ini(text) == {"a": {"x": "1", "y": "two words", "z": "a;b"}}


def test_continuation_lines() -> None:
    text = "[a]\nk = first\n    second\n    third\nj = done\n"
    assert parse_ini(text) == {"a": {"k": "first second third", "j": "done"}}


def test_empty_continuation_adds_nothing() -> None:
    assert parse_ini("[a]\nk = one\n   \n") == {"a": {"k": "one"}}


def test_duplicate_sections_merge() -> None:
    text = "[a]\nx = 1\nz = 0\n[a]\ny = 2\nx = 3\n"
    assert parse_ini(text) == {"a": {"x": "3", "z": "0", "y": "2"}}


def test_keys_before_first_section() -> None:
    text = "top = yes\n[s]\nk = 2\n"
    assert parse_ini(text) == {"": {"top": "yes"}, "s": {"k": "2"}}


def test_empty_value_and_colon_separator() -> None:
    assert parse_ini("[a]\nx =\ny:  \n") == {"a": {"x": "", "y": ""}}


@pytest.mark.parametrize("bad", ["[a\nx=1\n", "[ ]\n", "= value\n"])
def test_invalid_documents(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_ini(bad)
