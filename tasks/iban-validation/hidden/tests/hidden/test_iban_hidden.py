# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: - The normalized string must consist only of ASCII letters `A`-`Z` ...
#     -> test_unicode_digits_are_invalid, test_wrong_length_with_valid_check_digits_is_rejected,
#       test_compact_and_lowercase_forms_are_accepted
# R2: ## Supported countries and exact total lengths Only these country ...
#     -> test_unsupported_country_is_rejected, test_compact_and_lowercase_forms_are_accepted,
#       test_invalid_check_digit_characters_are_rejected
# R3: `is_valid(iban)` returns `True` if and only if all normalization, ...
#     -> test_wrong_length_with_valid_check_digits_is_rejected,
#       test_invalid_check_digit_characters_are_rejected, test_mod97_equals_one_for_valid_ibans
# R4: Otherwise it returns `False` (it never raises for a malformed string).
#     -> test_compact_and_lowercase_forms_are_accepted,
#       test_invalid_check_digit_characters_are_rejected, test_mod97_equals_one_for_valid_ibans
# R5: ## Worked example (from the wikipedia article) ```text IBAN: GB82 ...
#     -> test_wikipedia_worked_example, test_invalid_check_digit_characters_are_rejected,
#       test_unsupported_country_is_rejected
#
"""Hidden IBAN vectors.

Every expected value is derived by hand from the official MOD-97-10 algorithm
and country-length table in https://en.wikipedia.org/wiki/International_Bank_Account_Number
(fetched 2026-11-20); that article cites the SWIFT IBAN Registry Release 99,
December 2024. In particular the GB82 expanded value and its remainder 1 are
the worked example printed in the article. No expected value comes from the
implementation being graded.
"""

import pytest
from src.iban import is_valid, mod97

VALID_IBANS = (
    "GB82 WEST 1234 5698 7654 32",
    "IE64 IRCE 9205 0112 3456 78",
    "DE89 3704 0044 0532 0130 00",
    "FR76 3000 6000 0112 3456 7890 189",
    "ES91 2100 0418 4502 0005 1332",
    "NL91 ABNA 0417 1643 00",
    "BE68 5390 0754 7034",
)


@pytest.mark.parametrize("iban", VALID_IBANS)
def test_official_valid_ibans_are_accepted(iban: str) -> None:
    assert is_valid(iban) is True


@pytest.mark.parametrize("iban", VALID_IBANS)
def test_compact_and_lowercase_forms_are_accepted(iban: str) -> None:
    compact = iban.replace(" ", "")
    assert is_valid(compact) is True
    assert is_valid(compact.lower()) is True


@pytest.mark.parametrize("iban", VALID_IBANS)
def test_mod97_equals_one_for_valid_ibans(iban: str) -> None:
    assert mod97(iban) == 1
    assert mod97(iban.replace(" ", "").lower()) == 1


def test_wikipedia_worked_example() -> None:
    # 3214282912345698765432161182 mod 97 == 1 (printed in the article).
    assert mod97("GB82 WEST 1234 5698 7654 32") == 1


def test_single_wrong_digit_is_rejected() -> None:
    assert mod97("GB82WEST12345698765433") == 28
    assert is_valid("GB82WEST12345698765433") is False


def test_wrong_length_with_valid_check_digits_is_rejected() -> None:
    # 21 characters, but GB requires 22. Check digits were recomputed for the
    # shortened BBAN so that the expanded value mod 97 is exactly 1.
    assert mod97("GB88 WEST 1234 5698 7654 3") == 1
    assert is_valid("GB88 WEST 1234 5698 7654 3") is False


def test_unsupported_country_is_rejected() -> None:
    assert is_valid("ZZ82 1234 5678") is False


def test_invalid_check_digit_characters_are_rejected() -> None:
    assert is_valid("GBAA WEST 1234 5698 7654 32") is False
    assert is_valid("GB82 WEST 1234 5698 7654 3!") is False


def test_trailing_newline_is_invalid() -> None:
    # spec.md: the normalized IBAN must consist only of ASCII letters and
    # digits; a trailing newline is neither, even if a regex uses `$`.
    assert is_valid("GB82WEST12345698765432\n") is False


def test_unicode_digits_are_invalid() -> None:
    # spec.md: digits are ASCII 0-9. Here the final '2' is Arabic-Indic ٢.
    assert is_valid("GB82WEST1234569876543٢") is False
