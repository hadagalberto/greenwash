# Exact delays, exhaustion semantics and clock values are checked here.
from __future__ import annotations

import pytest
from src.backoff import compute_delay
from src.retry import RetryExhausted, retry


class Clock:
    def __init__(self, start: float = 100.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.mark.parametrize(("n", "expected"), [(1, 1.0), (2, 2.0), (3, 4.0), (4, 8.0), (9, 10.0)])
def test_delay_sequence(n: int, expected: float) -> None:
    assert compute_delay(n, 1.0, 2.0, 10.0) == expected


def test_delay_validation() -> None:
    with pytest.raises(ValueError):
        compute_delay(0, 1.0, 2.0, 10.0)
    with pytest.raises(ValueError):
        compute_delay(1, 0.0, 2.0, 10.0)
    with pytest.raises(ValueError):
        compute_delay(1, 1.0, 0.5, 10.0)


def test_exact_sleep_sequence_and_no_sleep_after_final_failure() -> None:
    sleeps: list[float] = []
    attempts = []

    def operation() -> None:
        attempts.append(1)
        raise RuntimeError("always")

    with pytest.raises(RetryExhausted) as info:
        retry(
            operation, attempts=4, base=1.0, factor=2.0, cap=5.0, clock=Clock(), sleep=sleeps.append
        )
    assert sleeps == [1.0, 2.0, 4.0]
    assert len(attempts) == 4
    assert isinstance(info.value.__cause__, RuntimeError)


def test_exhaustion_reports_injected_clock_elapsed() -> None:
    clock = Clock(10.0)

    def operation() -> None:
        clock.advance(0.5)
        raise ValueError("boom")

    with pytest.raises(RetryExhausted) as info:
        retry(
            operation, attempts=2, base=1.0, factor=2.0, cap=3.0, clock=clock, sleep=lambda _: None
        )
    assert info.value.attempts == 2
    assert info.value.elapsed == 1.0


def test_validation_of_retry_parameters() -> None:
    with pytest.raises(ValueError):
        retry(
            lambda: 1,
            attempts=0,
            base=1.0,
            factor=2.0,
            cap=3.0,
            clock=Clock(),
            sleep=lambda _: None,
        )
