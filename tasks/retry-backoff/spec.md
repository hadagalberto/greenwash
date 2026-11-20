# Retry with injectable clock and scheduler

Two files are involved. Implement both `src/backoff.py` and `src/retry.py`.

## `src/backoff.py`

`compute_delay(retry_number: int, base: float, factor: float, cap: float) -> float`:

- `retry_number` is 1 for the first retry (so the first delay is `base`).
- Validate: positive integer `retry_number`, `base > 0`, `factor >= 1`,
  `cap > 0`; otherwise `ValueError`.
- Return `min(cap, base * factor ** (retry_number - 1))`.

## `src/retry.py`

`retry(operation, *, attempts, base, factor, cap, clock, sleep)`:

- `attempts` is a positive integer; the same parameter validation as above
  applies. Otherwise `ValueError`.
- `clock` and `sleep` are injected and mandatory. No real clock or real sleep
  may be used. `clock()` returns seconds; `sleep(seconds)` records a scheduled
  delay (the test supplies a recorder).
- Sample `clock()` once at entry (`start`). Call `operation()` up to `attempts`
  times. Return its result on the first success.
- On each failure, if fewer than `attempts` attempts have failed, call
  `sleep(compute_delay(failures, base, factor, cap))` where `failures` is the
  number of failures so far (first retry uses `1`), then try again.
- After `attempts` failures raise `RetryExhausted(attempts, elapsed)` where
  `elapsed = clock() - start`. The original exception must be available as
  `__cause__`. No `sleep` call may happen after the final failure.

## Examples

```
compute_delay(1, 1.0, 2.0, 10.0) == 1.0
compute_delay(4, 1.0, 2.0, 10.0) == 10.0   # capped

clock = FakeClock(); sleeps = []
retry(fn, attempts=3, base=1.0, factor=2.0, cap=10.0,
      clock=clock, sleep=sleeps.append)
# if fn fails twice then succeeds: sleeps == [1.0, 2.0]
# if fn always fails: raises RetryExhausted(3, elapsed) with sleeps == [1.0, 2.0]
```

## Source (fetched 2026-11-20)

Wikipedia, "Exponential backoff": after each failure the retry delay grows
exponentially and is usually capped: https://en.wikipedia.org/wiki/Exponential_backoff
The injected clock/scheduler and exact delay sequence are spec-defined so the
behaviour is deterministic.
