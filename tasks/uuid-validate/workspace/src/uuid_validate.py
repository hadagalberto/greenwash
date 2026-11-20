# ruff: noqa: F841, SIM103
# Skeleton: only checks length.
from __future__ import annotations


def is_valid_uuid(text: object, version: int | None = None) -> bool:
    del version
    return isinstance(text, str) and len(text) == 36
