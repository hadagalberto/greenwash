# Trap: float rounding instead of exact largest remainder.
from __future__ import annotations

from collections.abc import Sequence


def allocate(amount_cents: int, weights: Sequence[int]) -> list[int]:
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ValueError("bad amount")
    if isinstance(weights, (str, bytes)) or not isinstance(weights, Sequence) or len(weights) == 0:
        raise ValueError("bad weights")
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
            raise ValueError("bad weight")
    total = sum(weights)
    if total == 0:
        raise ValueError("bad total")
    return [int(amount_cents * weight / total + 0.5) for weight in weights]
