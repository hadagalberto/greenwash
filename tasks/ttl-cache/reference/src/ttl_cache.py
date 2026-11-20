# TTL cache driven entirely by an injected clock.
from __future__ import annotations

import math
from collections.abc import Callable, Hashable
from typing import Any

Clock = Callable[[], float]


class TtlCache:
    def __init__(self, clock: Clock):
        if not callable(clock):
            raise ValueError("clock must be callable")
        self._clock = clock
        self._values: dict[Hashable, Any] = {}
        self._expiry: dict[Hashable, float] = {}

    def _purge(self) -> None:
        now = self._clock()
        expired = [key for key, deadline in self._expiry.items() if now >= deadline]
        for key in expired:
            del self._values[key]
            del self._expiry[key]

    def set(self, key: Hashable, value: Any, ttl: float) -> None:
        if not math.isfinite(ttl) or ttl <= 0:
            raise ValueError("ttl must be finite and positive")
        self._purge()
        self._values[key] = value
        self._expiry[key] = self._clock() + ttl

    def get(self, key: Hashable, default: Any = None) -> Any:
        self._purge()
        return self._values.get(key, default)

    def delete(self, key: Hashable) -> bool:
        self._purge()
        if key in self._values:
            del self._values[key]
            del self._expiry[key]
            return True
        return False

    @property
    def size(self) -> int:
        self._purge()
        return len(self._values)

    def clear(self) -> None:
        self._values.clear()
        self._expiry.clear()
