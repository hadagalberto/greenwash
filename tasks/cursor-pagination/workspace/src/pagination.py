# Skeleton: no cursor returned.
from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def paginate(items: Sequence[T], offset: int, limit: int) -> tuple[list[T], str | None]:
    return list(items[offset : offset + limit]), None


def decode_offset(token: str) -> int:
    del token
    return 0
