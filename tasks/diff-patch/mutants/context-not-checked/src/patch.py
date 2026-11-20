# Apply a unified diff to a list of logical lines (no trailing newlines).
from __future__ import annotations

from collections.abc import Sequence

from src.hunk import parse_hunk_header


def apply_patch(lines: Sequence[str], patch: Sequence[str]) -> list[str]:
    current = list(lines)
    index = 0
    while index < len(patch):
        header = patch[index]
        if not header.startswith("@@"):
            index += 1
            continue
        position = parse_hunk_header(header)
        index += 1
        old_lines: list[str] = []
        new_lines: list[str] = []
        while index < len(patch) and patch[index].startswith((" ", "-", "+")):
            item = patch[index]
            if item[0] == "-":
                old_lines.append(item[1:])
            elif item[0] == "+":
                new_lines.append(item[1:])
            else:
                new_lines.append(item[1:])
            index += 1
        while index < len(patch) and patch[index].startswith("\\ No newline"):
            index += 1
        if len(old_lines) != position.old_count or len(new_lines) != position.new_count:
            raise ValueError("hunk line counts do not match header")
        start = position.old_start - 1
        if start < 0 or start + len(old_lines) > len(current):
            raise ValueError("hunk outside document")
        if current[start : start + len(old_lines)] != old_lines:
            raise ValueError("hunk context mismatch")
        current[start : start + len(old_lines)] = new_lines
    return current
