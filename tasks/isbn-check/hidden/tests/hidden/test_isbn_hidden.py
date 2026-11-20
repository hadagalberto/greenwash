"""Hidden ISBN vectors.

Expected values are hand-derived from the rules in
https://en.wikipedia.org/wiki/ISBN. The values for 0-306-40615-2 (sum 130,
check 2), 0-8044-2957-X (value 10 written as X) and 978-3-16-148410-0 are
published Wikipedia examples. No expected value is produced by executing a
solution file.
"""

from src.isbn import is_valid, isbn10_check_digit


def test_isbn10_check_digit_two() -> None:
    assert isbn10_check_digit("030640615") == "2"


def test_isbn10_check_digit_x() -> None:
    assert isbn10_check_digit("080442957") == "X"


def test_hyphenated_isbn10_is_valid() -> None:
    assert is_valid("0-306-40615-2") is True


def test_space_separated_isbn10_is_valid() -> None:
    assert is_valid("0 306 40615 2") is True


def test_hyphenated_isbn10_with_x_is_valid() -> None:
    assert is_valid("0-8044-2957-X") is True


def test_lowercase_x_is_invalid() -> None:
    assert is_valid("0-8044-2957-x") is False


def test_unseparated_lowercase_x_is_invalid() -> None:
    assert is_valid("080442957x") is False


def test_wrong_isbn10_check_digit_is_invalid() -> None:
    assert is_valid("0-306-40615-7") is False


def test_isbn13_infobox_example_is_valid() -> None:
    assert is_valid("978-3-16-148410-0") is True


def test_isbn13_unseparated_is_valid() -> None:
    assert is_valid("9780306406157") is True


def test_wrong_isbn13_check_digit_is_invalid() -> None:
    assert is_valid("978-3-16-148410-1") is False


def test_wrong_length_is_invalid() -> None:
    assert is_valid("030640615") is False


def test_non_digit_character_is_invalid() -> None:
    assert is_valid("0-306-40615-A") is False
