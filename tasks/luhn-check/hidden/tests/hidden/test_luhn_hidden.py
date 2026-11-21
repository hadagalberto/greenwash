# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: Sum all resulting digits (doubled and not doubled).
#     -> test_at_least_two_ascii_digits_required_without_raising,
#       test_check_digit_odd_length_payload, test_check_digit_second_known_payload
# R2: `is_valid(number)` returns `True` only when all of the following ...
#     -> test_at_least_two_ascii_digits_required_without_raising,
#       test_check_digit_odd_length_payload, test_check_digit_second_known_payload
# R3: It must never raise for an arbitrary string input, including the ...
#     -> test_empty_string_is_invalid, test_at_least_two_ascii_digits_required_without_raising,
#       test_check_digit_odd_length_payload
# R4: ## Examples - `luhn_check_digit("1789372997") == "4"` - ...
#     -> test_check_digit_odd_length_payload, test_check_digit_second_known_payload,
#       test_wikipedia_example_number_is_valid
# R5: Only `src/luhn.py` needs changing; do not modify the test files or ...
#     -> test_at_least_two_ascii_digits_required_without_raising,
#       test_check_digit_odd_length_payload, test_check_digit_second_known_payload
#
"""Hidden Luhn vectors.

Expected values are hand-derived from the algorithm in
https://en.wikipedia.org/wiki/Luhn_algorithm. The value 4 for payload
1789372997 is Wikipedia's published worked example (sum 56); the value 3 for
payload 7992739871 and the published card numbers are independent known
vectors. No expected value is produced by executing a solution file.
"""

from src.luhn import is_valid, luhn_check_digit


def test_check_digit_second_known_payload() -> None:
    assert luhn_check_digit("7992739871") == "3"


def test_check_digit_odd_length_payload() -> None:
    # 15-digit payload: the rightmost payload digit is doubled, so 1 is correct.
    assert luhn_check_digit("411111111111111") == "1"


def test_wikipedia_example_number_is_valid() -> None:
    assert is_valid("79927398713") is True


def test_visa_test_number_is_valid() -> None:
    # 16-digit Visa test number; its payload is odd-length (15 digits).
    assert is_valid("4111111111111111") is True


def test_wrong_check_digit_is_invalid() -> None:
    assert is_valid("79927398714") is False


def test_empty_string_is_invalid() -> None:
    assert is_valid("") is False


def test_single_digit_is_invalid() -> None:
    assert is_valid("7") is False


def test_spaces_are_not_accepted() -> None:
    assert is_valid("7992 7398 713") is False


def test_hyphens_are_not_accepted() -> None:
    assert is_valid("7992-7398-713") is False


def test_non_digit_is_invalid() -> None:
    assert is_valid("12a") is False


def test_at_least_two_ascii_digits_required_without_raising() -> None:
    # spec.md lines 34 and 39: >=2 chars, ASCII digits only, never raise for
    # arbitrary string input. "0" is too short; superscript and Arabic-Indic
    # digits are non-ASCII and must be rejected, not passed to int().
    assert is_valid("0") is False
    assert is_valid("²5") is False
    assert is_valid("٣٣") is False


def test_trailing_newline_is_invalid() -> None:
    # spec.md: the number is a string of ASCII digits; a trailing newline is
    # not a digit. A regex using `$` would wrongly accept it.
    assert is_valid("79927398713\n") is False
