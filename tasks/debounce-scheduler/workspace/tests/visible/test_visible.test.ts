// Visible tests use a single call and never flush or cancel.
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

test('single call fires once after the delay', () => {
  const scheduler = new FakeScheduler();
  const debouncer = new Debouncer(10, scheduler);
  let hits = 0;
  debouncer.call(() => { hits += 1; });
  scheduler.advance(10);
  assert.equal(hits, 1);
});

test('negative delay throws', () => {
  const scheduler = new FakeScheduler();
  assert.throws(() => new Debouncer(-1, scheduler), RangeError);
});
