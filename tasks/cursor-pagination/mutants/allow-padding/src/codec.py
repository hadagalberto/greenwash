# Strict unpadded base64url JSON cursors.
from __future__ import annotations

import base64
import binascii
import json
import re
from typing import Any

_URLSAFE = re.compile(r"^[A-Za-z0-9_-]+=*$")


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def decode_cursor(token: str) -> dict[str, Any]:
    if not isinstance(token, str) or not token or not _URLSAFE.fullmatch(token):
        raise ValueError("invalid cursor token")
    padding = "=" * (-len(token) % 4)
    try:
        raw = base64.urlsafe_b64decode(token + padding)
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid cursor token") from exc
    if not isinstance(payload, dict):
        raise ValueError("cursor payload must be an object")
    return payload
