# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: ## What `is_valid` must do - Hyphens `-` and spaces may appear ...
#     -> test_only_hyphens_and_spaces_may_be_removed, test_hyphenated_isbn10_is_valid,
#       test_hyphenated_isbn10_with_x_is_valid
# R2: - After removing hyphens and spaces, the remaining string must have ...
#     -> test_only_hyphens_and_spaces_may_be_removed, test_wrong_length_is_invalid,
#       test_hyphenated_isbn10_is_valid
# R3: - For length 10: the first 9 characters must be ASCII digits and the ...
#     -> test_isbn10_check_digit_x, test_lowercase_x_is_invalid, test_unicode_digits_are_rejected
# R4: The check character must equal `isbn10_check_digit(first_nine)`.
#     -> test_isbn10_check_digit_two, test_isbn10_check_digit_x,
#       test_wrong_isbn10_check_digit_is_invalid
# R5: - For length 13: all 13 characters must be ASCII digits and the last ...
#     -> test_isbn10_check_digit_two, test_isbn10_check_digit_x,
#       test_wrong_isbn10_check_digit_is_invalid
# R6: `is_valid` must return `False` (never raise) for empty strings, ...
#     -> test_wrong_isbn10_check_digit_is_invalid, test_wrong_isbn13_check_digit_is_invalid,
#       test_hyphenated_isbn10_is_valid
# R7: ## More examples - `is_valid("0-306-40615-2") is True` and ...
#     -> test_isbn10_check_digit_x, test_isbn13_infobox_example_is_valid,
#       test_wrong_isbn10_check_digit_is_invalid
# R8: Only `src/isbn.py` needs changing; do not modify the test files or ...
#     -> test_hyphenated_isbn10_is_valid, test_hyphenated_isbn10_with_x_is_valid,
#       test_isbn10_check_digit_two
#
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


def test_only_hyphens_and_spaces_may_be_removed() -> None:
    # spec.md: hyphens and spaces are ignored; a tab is "any other non-digit
    # character" and must invalidate the whole string.
    assert is_valid("978\t3161484100") is False


def test_unicode_digits_are_rejected() -> None:
    # spec.md: ISBN-13 is 13 ASCII digits. str.isdigit() accepts Arabic-Indic
    # digits, so stripping separators and calling isdigit() is not enough.
    assert is_valid("٩٧٨٣١٦١٤٨٤١٠" + "0") is False
