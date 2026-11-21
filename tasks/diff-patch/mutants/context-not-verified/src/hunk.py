# Parse unified-diff hunk headers.
from __future__ import annotations

import re
from dataclasses import dataclass

_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")


@dataclass(frozen=True)
class HunkRange:
    old_start: int
    old_count: int
    new_start: int
    new_count: int


def parse_hunk_header(header: str) -> HunkRange:
    match = _HEADER.fullmatch(header)
    if match is None:
        raise ValueError("malformed hunk header")
    old_start = int(match.group(1))
    old_count = 1 if match.group(2) is None else int(match.group(2))
    new_start = int(match.group(3))
    new_count = 1 if match.group(4) is None else int(match.group(4))
    if old_start < 1 or new_start < 1 or old_count < 0 or new_count < 0:
        raise ValueError("invalid hunk range")
    return HunkRange(old_start, old_count, new_start, new_count)
