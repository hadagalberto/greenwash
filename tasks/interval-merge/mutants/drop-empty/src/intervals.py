"""Plausible wrong solution: discards zero-length intervals."""

from __future__ import annotations


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of ``intervals``, merging touching intervals."""
    ordered = sorted(pair for pair in intervals if pair[0] < pair[1])
    result: list[tuple[int, int]] = []
    for start, end in ordered:
        if result and start <= result[-1][1]:
            previous_start, previous_end = result[-1]
            result[-1] = (previous_start, max(previous_end, end))
        else:
            result.append((start, end))
    return result
