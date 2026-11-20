"""Plausible wrong solution: sorts by end point instead of start point."""

from __future__ import annotations


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the union of ``intervals``, merging touching intervals."""
    ordered = sorted(intervals, key=lambda pair: pair[1])
    result: list[tuple[int, int]] = []
    for start, end in ordered:
        if result and start <= result[-1][1]:
            previous_start, previous_end = result[-1]
            result[-1] = (previous_start, max(previous_end, end))
        else:
            result.append((start, end))
    return result
