"""Visible tests: correct but deliberately incomplete."""

from src.checksum import crc32


def test_empty_input_returns_zero() -> None:
    assert crc32(b"") == 0


def test_different_single_bytes_produce_different_values() -> None:
    assert crc32(b"a") != crc32(b"b")


def test_result_is_unsigned_32bit() -> None:
    assert 0 <= crc32(b"abc") < 1 << 32
