# ruff: noqa: F841, SIM103
# RFC 4122 UUID string validation.
from __future__ import annotations

import re

_CANONICAL = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def is_valid_uuid(text: object, version: int | None = None) -> bool:
    if not isinstance(text, str):
        return False
    if _CANONICAL.fullmatch(text) is None:
        return False
    if version is not None and (isinstance(version, bool) or version not in (1, 2, 3, 4, 5)):
        return False
    variant_char = text[19]
    found_version = int(text[14], 16)
    if found_version not in (1, 2, 3, 4, 5):
        return False
    if version is not None and found_version != version:
        return False
    return True
