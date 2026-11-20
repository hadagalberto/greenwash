# Deterministic retry loop: clock and sleep are injected by the caller.
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.backoff import compute_delay

T = TypeVar("T")
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


class RetryExhausted(Exception):
    def __init__(self, attempts: int, elapsed: float):
        super().__init__(f"operation failed after {attempts} attempts")
        self.attempts = attempts
        self.elapsed = elapsed


def retry(
    operation: Callable[[], T],
    *,
    attempts: int,
    base: float,
    factor: float,
    cap: float,
    clock: Clock,
    sleep: Sleeper,
) -> T:
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError("attempts must be a positive integer")
    if base <= 0 or factor < 1 or cap <= 0:
        raise ValueError("invalid backoff parameters")
    start = 0.0
    failures = 0
    while True:
        try:
            return operation()
        except Exception as exc:
            failures += 1
            if failures >= attempts:
                raise RetryExhausted(attempts, clock() - start) from exc
            sleep(compute_delay(failures, base, factor, cap))
