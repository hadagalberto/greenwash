# Visible cases never refill past capacity, never overspend after a failure,
# and never move the clock backwards.
from src.token_bucket import TokenBucket


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_starts_full_and_enforces_capacity() -> None:
    bucket = TokenBucket(2.0, 0.0, Clock())
    assert bucket.allow() is True
    assert bucket.allow() is True
    assert bucket.allow() is False


def test_failed_allow_stays_failed_without_refill() -> None:
    bucket = TokenBucket(1.0, 0.0, Clock())
    assert bucket.allow() is True
    assert bucket.allow() is False
    assert bucket.allow() is False


def test_constructor_validation() -> None:
    for args in ((0.0, 1.0), (-1.0, 1.0), (1.0, -1.0)):
        try:
            TokenBucket(*args, Clock())
        except ValueError:
            continue
        raise AssertionError("expected ValueError")
