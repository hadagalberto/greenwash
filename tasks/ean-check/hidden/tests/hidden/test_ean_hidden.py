# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: `is_valid_ean13(code)` returns `True` only when `code` is exactly 13 ...
#     -> test_ean13_check_digit_gs1_official_example, test_ean13_check_digit_stabilo,
#       test_ean13_check_digit_wikipedia
# R2: `is_valid_upca(code)` returns `True` only when `code` is exactly 12 ...
#     -> test_upca_check_digit_official, test_upca_valid_code,
#       test_upca_zero_check_digit_but_wrong_is_invalid
# R3: Both validators must return `False` (never raise) for empty strings, ...
#     -> test_ean13_zero_check_digit_but_wrong_is_invalid,
#       test_upca_zero_check_digit_but_wrong_is_invalid,
#       test_ean13_check_digit_gs1_official_example
# R4: The two weight patterns must not be interchanged: EAN-13 starts with ...
#     -> test_ean13_check_digit_gs1_official_example, test_ean13_check_digit_stabilo,
#       test_ean13_check_digit_wikipedia
# R5: ## Extra examples - `ean13_check_digit("590123412345") == "7"` - ...
#     -> test_ean13_check_digit_gs1_official_example, test_ean13_check_digit_wikipedia,
#       test_ean13_check_digit_stabilo
# R6: Only `src/ean.py` needs changing; do not modify the test files or ...
#     -> test_ean13_check_digit_gs1_official_example, test_ean13_check_digit_stabilo,
#       test_ean13_check_digit_wikipedia
#
"""Hidden EAN-13 / UPC-A vectors.

Expected values are hand-derived from the published examples in
https://en.wikipedia.org/wiki/International_Article_Number (EAN-13
5901234123457 with sum 83 and check 7, and 4006381333931 with sum 89 and
check 1) and from the GS1 check-digit instructions at
https://www.gs1.org/how-calculate-check-digit-manually (GTIN-13
6291041500213 has weighted sum 57 and check digit 3). No expected value is
produced by executing a solution file.
"""

from src.ean import ean13_check_digit, is_valid_ean13, is_valid_upca, upca_check_digit


def test_ean13_check_digit_wikipedia() -> None:
    assert ean13_check_digit("590123412345") == "7"


def test_ean13_check_digit_stabilo() -> None:
    assert ean13_check_digit("400638133393") == "1"


def test_ean13_check_digit_gs1_official_example() -> None:
    # GS1 "How to calculate a check digit manually": 6+6+9+3+0+12+1+15+0+0+2+3 = 57.
    assert ean13_check_digit("629104150021") == "3"
    assert is_valid_ean13("6291041500213") is True


def test_upca_check_digit_official() -> None:
    assert upca_check_digit("03600029145") == "2"


def test_upca_valid_code() -> None:
    assert is_valid_upca("036000291452") is True


def test_ean13_zero_check_digit_but_wrong_is_invalid() -> None:
    # The correct check digit for payload 590123412345 is 7, not 0.
    assert is_valid_ean13("5901234123450") is False


def test_upca_zero_check_digit_but_wrong_is_invalid() -> None:
    # The correct check digit for payload 03600029145 is 2, not 0.
    assert is_valid_upca("036000291450") is False


def test_ean13_wrong_length_is_invalid() -> None:
    assert is_valid_ean13("59012341234567") is False


def test_upca_wrong_length_is_invalid() -> None:
    assert is_valid_upca("03600029145") is False


def test_ean13_non_digit_is_invalid() -> None:
    assert is_valid_ean13("59012341234a") is False


def test_ean13_separator_is_invalid() -> None:
    assert is_valid_ean13("590-1234123457") is False


def test_trailing_newline_is_invalid() -> None:
    # spec.md: the code consists of ASCII digits only; `$`-anchored regexes
    # accept a final newline.
    assert is_valid_ean13("5901234123457\n") is False
    assert is_valid_upca("036000291452\n") is False


def test_unicode_digits_are_invalid() -> None:
    # spec.md: all characters must be ASCII digits 0-9.
    assert is_valid_ean13("٥٩٠١٢٣٤١٢٣٤٥٧") is False
    assert is_valid_upca("٠٣٦٠٠٠٢٩١٤٥٢") is False
