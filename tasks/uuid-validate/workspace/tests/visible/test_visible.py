# ruff: noqa: F841, SIM103
# Visible cases are canonical v4 strings and obviously wrong lengths.
from src.uuid_validate import is_valid_uuid


def test_canonical_v4() -> None:
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True


def test_wrong_length() -> None:
    assert is_valid_uuid("550e8400-e29b-41d4-a716") is False


def test_version_filter_on_valid_v4() -> None:
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000", 4) is True


def test_non_string() -> None:
    assert is_valid_uuid(None) is False
