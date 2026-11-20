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
