# Visible tests never advance the clock, so expiry bugs are invisible.
from src.ttl_cache import TtlCache


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_set_and_get() -> None:
    cache = TtlCache(Clock())
    cache.set("a", 1, 10.0)
    assert cache.get("a") == 1
    assert cache.size == 1


def test_missing_key_returns_default() -> None:
    cache = TtlCache(Clock())
    assert cache.get("absent") is None
    assert cache.get("absent", 7) == 7


def test_delete_and_clear() -> None:
    cache = TtlCache(Clock())
    cache.set("a", 1, 10.0)
    assert cache.delete("a") is True
    assert cache.delete("a") is False
    cache.set("b", 2, 10.0)
    cache.clear()
    assert cache.size == 0
