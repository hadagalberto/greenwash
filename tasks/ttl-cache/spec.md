# TTL cache

Implement `TtlCache` in `src/ttl_cache.py`.

```py
class TtlCache:
    def __init__(self, clock: Callable[[], float]): ...
    def set(self, key: Hashable, value: Any, ttl: float) -> None: ...
    def get(self, key: Hashable, default: Any = None) -> Any: ...
    def delete(self, key: Hashable) -> bool: ...
    @property
    def size(self) -> int: ...
    def clear(self) -> None: ...
```

## Contract

- Time comes only from the injected `clock()` (seconds). Tests inject a fake
  clock; no real time is read. Non-callable clock raises `ValueError`.
- `ttl` must be finite and `> 0`, otherwise `ValueError`.
- `set` stores `value` under `key` with deadline `clock() + ttl`. Setting an
  existing key replaces the value and resets the deadline.
- An entry is **expired** when `clock() >= deadline` (the boundary is expired).
- `get`, `set`, `delete` and `size` first purge every expired entry, then act.
  `get` returns `default` (default `None`) for a missing or expired key.
- `delete` returns `True` only if a live entry existed.
- `clear` removes all entries without consulting the clock.
- If the clock moves backwards, no entry becomes expired because of it.

## Examples (clock starts at 0.0)

```
c = TtlCache(clock)
c.set('a', 1, 10.0)
c.get('a') -> 1; c.size -> 1
clock.now = 10.0
c.get('a') -> None; c.size -> 0
c.set('b', 2, 5.0); clock.now = 4.0; c.set('b', 3, 5.0)
clock.now = 8.0
c.get('b') -> 3   # deadline was refreshed to 9.0
```

## Source (fetched 2026-11-20)

Wikipedia, "Cache replacement policies": time-to-lived caches expire entries
after a fixed lifetime measured from insertion:
https://en.wikipedia.org/wiki/Cache_replacement_policies
The exact boundary and injected-clock rules are spec-defined.
