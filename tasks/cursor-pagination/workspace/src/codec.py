# Skeleton: identity token.
from __future__ import annotations

from typing import Any


def encode_cursor(payload: dict[str, Any]) -> str:
    del payload
    return ""


def decode_cursor(token: str) -> dict[str, Any]:
    del token
    return {}
