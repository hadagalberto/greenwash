# Hand-computed expiry vectors with a fully injected clock.
import pytest
from src.ttl_cache import TtlCache


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_expiry_boundary_is_inclusive() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("a", 1, 10.0)
    clock.now = 9.999
    assert cache.get("a") == 1
    clock.now = 10.0
    assert cache.get("a") is None
    assert cache.size == 0


def test_set_refreshes_deadline() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("b", 1, 5.0)
    clock.now = 4.0
    cache.set("b", 2, 5.0)
    clock.now = 8.0
    assert cache.get("b") == 2
    clock.now = 9.0
    assert cache.get("b") is None


def test_size_drops_expired_entries_without_other_calls() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("only", 1, 2.0)
    clock.now = 2.0
    assert cache.size == 0


def test_purge_affects_delete_and_size() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("x", 1, 1.0)
    cache.set("y", 2, 100.0)
    clock.now = 1.0
    assert cache.delete("x") is False
    assert cache.size == 1
    assert cache.delete("y") is True


def test_backwards_clock_keeps_entries() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("k", "v", 10.0)
    clock.now = 5.0
    clock.now = -5.0
    assert cache.get("k") == "v"


def test_invalid_ttl() -> None:
    cache = TtlCache(Clock())
    with pytest.raises(ValueError):
        cache.set("k", "v", 0.0)
    with pytest.raises(ValueError):
        cache.set("k", "v", float("nan"))
