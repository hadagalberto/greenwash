# Debouncer with an injected scheduler

Implement `src/scheduler.ts` and `src/debounce.ts`.

## `src/scheduler.ts`

```ts
export interface Scheduler {
  now(): number;
  schedule(fn: () => void, delayMs: number): number;  // returns a handle
  cancel(handle: number): void;
}
```

## `src/debounce.ts`

```ts
export class Debouncer {
  constructor(delayMs: number, scheduler: Scheduler);
  get pendingCount(): number;
  call(fn: () => void): void;
  flush(): void;
  cancel(): void;
}
```

## Contract

- `delayMs` must be finite and `>= 0`, else `RangeError`. `call` with a
  non-function throws `TypeError`.
- No real timer or real clock may be used: all timing goes through the injected
  `scheduler`.
- `call(fn)` is trailing edge: cancel any pending timer, store `fn`, and
  schedule it for `delayMs` milliseconds after the call. Calling again resets
  the timer and replaces the pending callback.
- When the timer fires, the pending callback runs exactly once and the internal
  state becomes empty.
- `flush()` cancels the timer and runs the pending callback immediately (if
  any). `cancel()` cancels the timer and discards the callback without running
  it. Both leave `pendingCount === 0`.
- `pendingCount` is `1` while a callback is waiting, otherwise `0`.

## Example (FakeScheduler with `now()` starting at 0)

```
const d = new Debouncer(10, scheduler);
d.call(() => hits.push('a'));
scheduler.advance(6);
d.call(() => hits.push('b'));
scheduler.advance(9);  // nothing yet: timer reset at t=6
assert.equal(hits.length, 0);
scheduler.advance(1);
assert.deepEqual(hits, ['b']);
```

## Source (fetched 2026-11-20)

MDN, `Window.setTimeout`: schedules a callback after a delay and returns an id
that can be passed to `clearTimeout` to cancel it:
https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout
The injectable interface and exact reset semantics here are spec-defined.
