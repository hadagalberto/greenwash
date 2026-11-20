# All vectors are computed by hand from the spec; the clock never reads real time.
import pytest
from src.token_bucket import TokenBucket


class Clock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_refill_is_capped_at_capacity() -> None:
    clock = Clock()
    bucket = TokenBucket(3.0, 10.0, clock)
    assert [bucket.allow() for _ in range(3)] == [True, True, True]
    clock.advance(100.0)
    assert [bucket.allow() for _ in range(3)] == [True, True, True]
    assert bucket.allow() is False


def test_failed_allow_consumes_nothing() -> None:
    clock = Clock()
    bucket = TokenBucket(1.0, 1.0, clock)
    assert bucket.allow() is True
    assert bucket.allow() is False
    assert bucket.tokens == 0.0
    clock.advance(1.0)
    assert bucket.allow() is True
    assert bucket.allow() is False


def test_fractional_refill_is_deterministic() -> None:
    clock = Clock()
    bucket = TokenBucket(2.0, 2.0, clock)
    assert bucket.allow() is True
    assert bucket.allow() is True
    clock.advance(0.5)
    assert bucket.tokens == 1.0
    assert bucket.allow() is True
    assert bucket.allow() is False


def test_backwards_clock_never_removes_tokens() -> None:
    clock = Clock()
    bucket = TokenBucket(2.0, 1.0, clock)
    assert bucket.allow() is True
    assert bucket.allow() is True
    clock.advance(5.0)
    assert bucket.tokens == 2.0
    clock.advance(-5.0)
    assert bucket.tokens == 2.0


def test_custom_cost() -> None:
    clock = Clock()
    bucket = TokenBucket(5.0, 1.0, clock)
    assert bucket.allow(2.5) is True
    assert bucket.allow(3.0) is False
    assert bucket.tokens == 2.5
    with pytest.raises(ValueError):
        bucket.allow(0.0)
