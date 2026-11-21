# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: ``` ## Contract - Time comes only from the injected `clock()` (seconds).
#     -> test_backwards_clock_keeps_entries, test_spec_example_and_non_callable_clock,
#       test_expiry_boundary_is_inclusive
# R2: - `ttl` must be finite and `> 0`, otherwise `ValueError`.
#     -> test_invalid_ttl, test_backwards_clock_keeps_entries, test_expiry_boundary_is_inclusive
# R3: - `delete` returns `True` only if a live entry existed.
#     -> test_purge_affects_delete_and_size, test_backwards_clock_keeps_entries,
#       test_expiry_boundary_is_inclusive
#
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


def test_spec_example_and_non_callable_clock() -> None:
    # Expected values are quoted verbatim in the task spec.
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("a", 1, 10.0)
    assert cache.get("a") == 1
    assert cache.size == 1
    clock.now = 10.0
    assert cache.get("a") is None
    assert cache.size == 0
    with pytest.raises(ValueError):
        TtlCache(None)  # type: ignore[arg-type]


def test_get_default_and_clear() -> None:
    clock = Clock()
    cache = TtlCache(clock)
    cache.set("a", 1, 10.0)
    assert cache.get("missing") is None
    assert cache.get("missing", "fallback") == "fallback"
    cache.clear()
    assert cache.size == 0
    assert cache.get("a") is None
