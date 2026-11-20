# Incomplete starting point: ignores the remainder rule.
from __future__ import annotations

from collections.abc import Sequence


def allocate(amount_cents: int, weights: Sequence[int]) -> list[int]:
    total = sum(weights)
    return [amount_cents * weight // total for weight in weights]
