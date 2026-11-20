# Sliding-window rate limiter

Implement `src/limiter.ts` exporting:

```ts
export class SlidingWindowLimiter {
  constructor(maxEvents: number, windowMs: number, clock: () => number);
  allow(key?: string): boolean;
  count(key?: string): number;
}
```

## Contract

- `maxEvents` must be a positive integer, `windowMs` a positive finite number,
  and `clock` a function; otherwise throw `RangeError`.
- All time comes from `clock()` (milliseconds). Tests inject a fake clock. No
  real-time source may be used.
- Events are tracked per key (default `'default'`). Before each `allow` or
  `count`, discard events whose timestamp `<= now - windowMs` (the window is
  half-open: an event exactly `windowMs` old has expired).
- `allow` returns `true` and records `now` when fewer than `maxEvents` events
  remain in the window. Otherwise it returns `false` and records **nothing**.
- `count` returns the number of live events without recording anything.

## Examples (clock starts at 0)

```
const limiter = new SlidingWindowLimiter(2, 1000, clock);
limiter.allow() -> true; limiter.allow() -> true; limiter.allow() -> false
clock.now = 500; limiter.allow() -> false
clock.now = 1000; limiter.allow() -> true; limiter.count() -> 2
limiter.allow('other') -> true   // separate key
```

## Source (fetched 2026-11-20)

Wikipedia, "Sliding window protocol": a window advances with the passage of
time rather than resetting on fixed boundaries:
https://en.wikipedia.org/wiki/Sliding_window_protocol
The exact boundary and injected-clock rules here are spec-defined.
