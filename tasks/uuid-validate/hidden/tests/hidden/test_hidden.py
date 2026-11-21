# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: Return a bool; never raise for malformed input.
#     -> test_invalid_uuids, test_invalid_version_argument,
#       test_never_raises_for_arbitrary_objects
# R2: ## Rules (RFC 4122) - The string must match exactly `8-4-4-4-12` ...
#     -> test_variant_boundary_digits, test_version_boundary_digits, test_invalid_uuids
# R3: In the string this is the first hex digit of the fourth group; RFC ...
#     -> test_variant_boundary_digits, test_invalid_uuids, test_invalid_version_argument
# R4: It must be `1`, `2`, `3`, `4` or `5`.
#     -> test_invalid_uuids, test_invalid_version_argument,
#       test_never_raises_for_arbitrary_objects
# R5: - If `version` is supplied it must be an `int` (not `bool`) in ...
#     -> test_invalid_version_argument, test_version_boundary_digits, test_version_matching
#
# ruff: noqa: F841, SIM103
# Vectors taken from RFC 4122 section 3 and its variant/version tables.
import pytest
from src.uuid_validate import is_valid_uuid

VALID = (
    "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
    "550e8400-e29b-41d4-a716-446655440000",
    "3F2504E0-4F89-11D3-9A0C-0305E82C3301",
    "00000000-0000-4000-8000-000000000000",
    "00000000-0000-5000-b000-000000000000",
)

INVALID = (
    "550e8400e29b41d4a716446655440000",
    "{550e8400-e29b-41d4-a716-446655440000}",
    "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-c716-446655440000",
    "550e8400-e29b-61d4-a716-446655440000",
    "00000000-0000-0000-0000-000000000000",
    "550e8400-e29b-41d4-a716-44665544000g",
    " 550e8400-e29b-41d4-a716-446655440000",
    # spec.md: "no whitespace"; a regex using `$` (not fullmatch) accepts this.
    "550e8400-e29b-41d4-a716-446655440000\n",
)


@pytest.mark.parametrize("value", VALID)
def test_valid_uuids(value: str) -> None:
    assert is_valid_uuid(value) is True


@pytest.mark.parametrize("value", INVALID)
def test_invalid_uuids(value: str) -> None:
    assert is_valid_uuid(value) is False


def test_version_matching() -> None:
    # spec.md: `version` must be an int, not bool. True == 1, so a bool passes
    # any `version in 1..5` check unless explicitly rejected.
    assert is_valid_uuid(VALID[0], True) is False  # type: ignore[arg-type]
    assert is_valid_uuid(VALID[0], 1) is True
    assert is_valid_uuid(VALID[0], 4) is False
    assert is_valid_uuid(VALID[4], 5) is True
    assert is_valid_uuid(VALID[4], 1) is False


@pytest.mark.parametrize("bad_version", [0, 6, True, "4"])
def test_invalid_version_argument(bad_version: object) -> None:
    assert is_valid_uuid(VALID[1], bad_version) is False  # type: ignore[arg-type]


def test_spec_examples() -> None:
    # Every expectation is quoted verbatim in the spec.md Examples block.
    assert is_valid_uuid("f81d4fae-7dec-11d0-a765-00a0c91e6bf6") is True
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000", 1) is False
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000", 4) is True
    assert is_valid_uuid("550e8400e29b41d4a716446655440000") is False
    assert is_valid_uuid("{550e8400-e29b-41d4-a716-446655440000}") is False
    assert is_valid_uuid("550e8400-e29b-41d4-c716-446655440000") is False
    assert is_valid_uuid("00000000-0000-0000-0000-000000000000") is False


def test_variant_boundary_digits() -> None:
    # spec.md: the fourth group's first hex digit must be 8, 9, a or b.
    assert is_valid_uuid("00000000-0000-4000-9000-000000000000") is True
    assert is_valid_uuid("00000000-0000-4000-a000-000000000000") is True
    assert is_valid_uuid("00000000-0000-4000-b000-000000000000") is True
    assert is_valid_uuid("00000000-0000-4000-c000-000000000000") is False


def test_version_boundary_digits() -> None:
    # spec.md: the third group's first hex digit must be 1..5.
    assert is_valid_uuid("00000000-0000-1000-8000-000000000000") is True
    assert is_valid_uuid("00000000-0000-5000-8000-000000000000") is True
    assert is_valid_uuid("00000000-0000-6000-8000-000000000000") is False


def test_never_raises_for_arbitrary_objects() -> None:
    # spec.md: return a bool; never raise for malformed input.
    for value in (None, 42, b"abc", [], {}, "", "abc"):
        assert is_valid_uuid(value) is False
