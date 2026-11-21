// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: # Sliding-window rate limiter Implement `src/limiter.ts` exporting: ...
//     -> constructor validates all three arguments, count records nothing, expired events are
//       pruned by count
//
// All vectors use a fully controlled clock.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { SlidingWindowLimiter } from '../../src/limiter.ts';

class Clock {
  now = 0;
  clock = () => this.now;
}

test('partial advance does not free a slot', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(2, 1000, c.clock);
  assert.equal(limiter.allow(), true);
  c.now = 500;
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), false);
});

test('window boundary is half-open', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(2, 1000, c.clock);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), true);
  c.now = 999;
  assert.equal(limiter.allow(), false);
  c.now = 1000;
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.count(), 1);
});

test('rejected events are not recorded', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(1, 1000, c.clock);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), false);
  c.now = 1000;
  assert.equal(limiter.allow(), true);
});

test('keys are independent', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(1, 1000, c.clock);
  assert.equal(limiter.allow('a'), true);
  assert.equal(limiter.allow('a'), false);
  assert.equal(limiter.allow('b'), true);
  assert.equal(limiter.count('a'), 1);
  assert.equal(limiter.count('b'), 1);
});

test('spec example sequence', () => {
  // Allow decisions are quoted verbatim in the task spec. The t=0 events are
  // exactly windowMs old at t=1000, so the half-open rule expires both of them
  // and only the newly admitted event remains live.
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(2, 1000, c.clock);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), false);
  c.now = 500;
  assert.equal(limiter.allow(), false);
  c.now = 1000;
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.count(), 1);
  assert.equal(limiter.allow('other'), true);
});

test('constructor validates all three arguments', () => {
  // spec.md: maxEvents positive integer, windowMs positive finite, clock fn.
  const c = new Clock();
  assert.throws(() => new SlidingWindowLimiter(0, 1000, c.clock), RangeError);
  assert.throws(() => new SlidingWindowLimiter(1.5, 1000, c.clock), RangeError);
  assert.throws(() => new SlidingWindowLimiter(1, 0, c.clock), RangeError);
  assert.throws(() => new SlidingWindowLimiter(1, Infinity, c.clock), RangeError);
  assert.throws(() => new SlidingWindowLimiter(1, 1000, undefined as unknown as () => number), RangeError);
});

test('count records nothing', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(1, 1000, c.clock);
  assert.equal(limiter.count(), 0);
  assert.equal(limiter.count(), 0);
  assert.equal(limiter.allow(), true);
});

test('expired events are pruned by count', () => {
  const c = new Clock();
  const limiter = new SlidingWindowLimiter(2, 1000, c.clock);
  limiter.allow();
  c.now = 1000;
  assert.equal(limiter.count(), 0);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), false);
});
