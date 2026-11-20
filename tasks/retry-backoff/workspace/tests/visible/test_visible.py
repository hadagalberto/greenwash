# Visible cases check success and count of retries, not exact delay values.
from src.backoff import compute_delay
from src.retry import retry


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_success_first_try_does_not_sleep() -> None:
    sleeps: list[float] = []
    assert (
        retry(
            lambda: 42,
            attempts=3,
            base=1.0,
            factor=2.0,
            cap=10.0,
            clock=Clock(),
            sleep=sleeps.append,
        )
        == 42
    )
    assert sleeps == []


def test_succeeds_on_second_attempt() -> None:
    calls = []
    sleeps: list[float] = []

    def operation() -> int:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("first")
        return 7

    assert (
        retry(
            operation,
            attempts=3,
            base=1.0,
            factor=2.0,
            cap=10.0,
            clock=Clock(),
            sleep=sleeps.append,
        )
        == 7
    )
    assert len(calls) == 2
    assert len(sleeps) == 1


def test_delay_helper_is_positive() -> None:
    assert compute_delay(1, 1.0, 2.0, 10.0) > 0.0
