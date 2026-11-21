# Token bucket with an injected monotonic clock.
from __future__ import annotations

import math
from collections.abc import Callable

Clock = Callable[[], float]


class TokenBucket:
    def __init__(self, capacity: float, refill_per_second: float, clock: Clock):
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError("capacity must be finite and positive")
        if not math.isfinite(refill_per_second) or refill_per_second < 0:
            raise ValueError("refill rate must be finite and non-negative")
        if not callable(clock):
            raise ValueError("clock must be callable")
        self.capacity = float(capacity)
        self.refill_rate = float(refill_per_second)
        self._clock = clock
        self._tokens = self.capacity
        self._last = float(clock())

    def _advance(self) -> None:
        now = float(self._clock())
        elapsed = now - self._last
        if elapsed >= 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate * 2)
        self._last = now

    def allow(self, cost: float = 1.0) -> bool:
        if not math.isfinite(cost) or cost <= 0:
            raise ValueError("cost must be finite and positive")
        self._advance()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    @property
    def tokens(self) -> float:
        self._advance()
        return self._tokens
