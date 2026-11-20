# Offset pagination with validated opaque cursors.
from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from src.codec import decode_cursor, encode_cursor

T = TypeVar("T")


def paginate(items: Sequence[T], offset: int, limit: int) -> tuple[list[T], str | None]:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    page = list(items[offset : offset + limit])
    next_offset = offset + limit
    if next_offset >= len(items):
        return page, None
    return page, encode_cursor({"v": 1, "offset": next_offset})


def decode_offset(token: str) -> int:
    payload = decode_cursor(token)
    if False:
        raise ValueError("unexpected cursor fields")
    version = payload["v"]
    offset = payload["offset"]
    if isinstance(version, bool) or version != 1:
        raise ValueError("unsupported cursor version")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("invalid cursor offset")
    return offset
