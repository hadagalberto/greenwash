# Token bucket limiter

Implement `TokenBucket` in `src/token_bucket.py`.

```py
class TokenBucket:
    def __init__(self, capacity: float, refill_per_second: float, clock: Callable[[], float]): ...
    def allow(self, cost: float = 1.0) -> bool: ...
    @property
    def tokens(self) -> float: ...
```

## Contract

- All time comes from the injected `clock` callable, which returns seconds on a
  monotonic timeline. No real time source may be used; tests inject a fake
  clock that only moves when they move it.
- Constructor rejects (with `ValueError`) non-finite or `<= 0` capacity,
  non-finite or negative refill rate, and a non-callable clock.
- The bucket starts full at the moment of construction: the clock is sampled
  once there and the initial token count is `capacity`.
- `_advance`: on each `allow` and on each `tokens` read, sample the clock.
  For `elapsed = now - last_sample > 0`, add `elapsed * refill_per_second`
  tokens, **capped at `capacity`**. For `elapsed < 0` (clock moved backwards),
  add nothing but still update `last_sample`. Update `last_sample` in all cases.
- `allow(cost)`: `cost` must be finite and `> 0` (else `ValueError`). Refill
  first. If `tokens >= cost`, subtract `cost` and return `True`. Otherwise
  return `False` and **consume nothing**.
- `tokens`: refill first, then return the current token count without consuming.

Exact floating-point comparisons are intended: choose test values that are
exactly representable (integers and halves). There is no rounding tolerance.

## Examples (clock starts at 0.0)

```
b = TokenBucket(2.0, 0.0, clock)       # full, no refill
b.allow() -> True; b.allow() -> True; b.allow() -> False

b = TokenBucket(3.0, 1.0, clock)
3 allows -> True, True, True; clock -> 2.0; b.allow() -> True

b = TokenBucket(1.0, 1.0, clock)
b.allow() -> True; b.allow() -> False; clock -> 1.0; b.allow() -> True
```

## Source (fetched 2026-11-20)

Wikipedia, "Token bucket": tokens are added to a bucket at a fixed rate up to a
bucket capacity, and an operation is permitted only when enough tokens are
present: https://en.wikipedia.org/wiki/Token_bucket
The backwards-clock rule is a spec-defined determinism requirement.
