# Skeleton: ignores all counts.
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HunkRange:
    old_start: int
    old_count: int
    new_start: int
    new_count: int


def parse_hunk_header(header: str) -> HunkRange:
    del header
    return HunkRange(1, 1, 1, 1)
