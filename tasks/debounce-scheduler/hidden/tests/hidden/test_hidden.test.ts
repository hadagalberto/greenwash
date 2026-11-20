// Reset, flush and cancel behaviour checked with the controlled scheduler.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Debouncer } from '../../src/debounce.ts';
import type { Scheduler } from '../../src/scheduler.ts';

class FakeScheduler implements Scheduler {
  nowMs = 0;
  private nextHandle = 1;
  private readonly tasks = new Map<number, { due: number; fn: () => void }>();

  now(): number {
    return this.nowMs;
  }

  schedule(fn: () => void, delayMs: number): number {
    const handle = this.nextHandle++;
    this.tasks.set(handle, { due: this.nowMs + delayMs, fn });
    return handle;
  }

  cancel(handle: number): void {
    this.tasks.delete(handle);
  }

  advance(ms: number): void {
    this.nowMs += ms;
    const due = [...this.tasks.entries()].filter(([, task]) => task.due <= this.nowMs);
    for (const [handle, task] of due) {
      this.tasks.delete(handle);
      task.fn();
    }
  }
}

test('second call resets the timer and replaces the callback', () => {
  const scheduler = new FakeScheduler();
  const debouncer = new Debouncer(10, scheduler);
  const hits: string[] = [];
  debouncer.call(() => hits.push('a'));
  scheduler.advance(6);
  assert.equal(debouncer.pendingCount, 1);
  debouncer.call(() => hits.push('b'));
  scheduler.advance(9);
  assert.deepEqual(hits, []);
  scheduler.advance(1);
  assert.deepEqual(hits, ['b']);
  assert.equal(debouncer.pendingCount, 0);
});

test('flush runs the pending callback immediately', () => {
  const scheduler = new FakeScheduler();
  const debouncer = new Debouncer(100, scheduler);
  let hits = 0;
  debouncer.call(() => { hits += 1; });
  debouncer.flush();
  assert.equal(hits, 1);
  assert.equal(debouncer.pendingCount, 0);
  scheduler.advance(1000);
  assert.equal(hits, 1);
});

test('cancel discards the pending callback', () => {
  const scheduler = new FakeScheduler();
  const debouncer = new Debouncer(100, scheduler);
  let hits = 0;
  debouncer.call(() => { hits += 1; });
  debouncer.cancel();
  scheduler.advance(1000);
  assert.equal(hits, 0);
  assert.equal(debouncer.pendingCount, 0);
});

test('calling a non-function throws TypeError', () => {
  const debouncer = new Debouncer(1, new FakeScheduler());
  assert.throws(() => debouncer.call(42 as unknown as () => void), TypeError);
});
