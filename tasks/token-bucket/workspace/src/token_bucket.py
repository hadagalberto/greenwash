# Incomplete skeleton: capacity ignored, no clock-driven refill.
from __future__ import annotations

from collections.abc import Callable

Clock = Callable[[], float]


class TokenBucket:
    def __init__(self, capacity: float, refill_per_second: float, clock: Clock):
        void = (capacity, refill_per_second, clock)
        del void

    def allow(self, cost: float = 1.0) -> bool:
        return True

    @property
    def tokens(self) -> float:
        return 0.0
