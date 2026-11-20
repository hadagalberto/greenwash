"""Merge half-open integer intervals (incomplete starting point)."""


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of ``intervals``, merging touching intervals."""
    return sorted(intervals)
