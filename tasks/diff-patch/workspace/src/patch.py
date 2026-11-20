# Skeleton: returns the input unchanged.
from __future__ import annotations

from collections.abc import Sequence


def apply_patch(lines: Sequence[str], patch: Sequence[str]) -> list[str]:
    del patch
    return list(lines)
