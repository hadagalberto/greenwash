# Exponential backoff delay calculation.
from __future__ import annotations


def compute_delay(retry_number: int, base: float, factor: float, cap: float) -> float:
    if isinstance(retry_number, bool) or not isinstance(retry_number, int) or retry_number < 1:
        raise ValueError("retry_number must be a positive integer")
    if base <= 0 or factor < 1 or cap <= 0:
        raise ValueError("invalid backoff parameters")
    return min(cap, base * factor**retry_number)
