# Skeleton: no expiry, clock ignored.
from __future__ import annotations

from collections.abc import Callable, Hashable
from typing import Any


class TtlCache:
    def __init__(self, clock: Callable[[], float]) -> None:
        del clock
        self._values: dict[Hashable, Any] = {}

    def set(self, key: Hashable, value: Any, ttl: float) -> None:
        self._values[key] = value

    def get(self, key: Hashable, default: Any = None) -> Any:
        return self._values.get(key, default)

    def delete(self, key: Hashable) -> bool:
        return self._values.pop(key, None) is not None

    @property
    def size(self) -> int:
        return len(self._values)

    def clear(self) -> None:
        self._values.clear()
