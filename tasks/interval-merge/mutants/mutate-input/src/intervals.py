"""Plausible wrong solution: sorts the caller's list in place."""

from __future__ import annotations


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of ``intervals``, merging touching intervals."""
    intervals.sort()
    result: list[tuple[int, int]] = []
    for start, end in intervals:
        if result and start <= result[-1][1]:
            previous_start, previous_end = result[-1]
            result[-1] = (previous_start, max(previous_end, end))
        else:
            result.append((start, end))
    return result
