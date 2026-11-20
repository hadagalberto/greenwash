# Allocate integer cents proportionally with the largest-remainder rule.
from __future__ import annotations

from collections.abc import Sequence


def allocate(amount_cents: int, weights: Sequence[int]) -> list[int]:
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ValueError("amount_cents must be a non-negative integer")
    if isinstance(weights, (str, bytes)) or not isinstance(weights, Sequence) or len(weights) == 0:
        raise ValueError("weights must be a non-empty sequence")
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
            raise ValueError("weights must be non-negative integers")
    total = sum(weights)
    if total == 0:
        raise ValueError("total weight must be positive")
    products = [amount_cents * weight for weight in weights]
    result = [product // total for product in products]
    remainders = [product % total for product in products]
    leftover = amount_cents - sum(result)
    order = sorted(range(len(weights)), key=lambda i: (-remainders[i], -i))
    for index in order[:leftover]:
        result[index] += 1
    return result
