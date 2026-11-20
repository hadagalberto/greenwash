// Visible cases never move the clock and never exceed the window twice.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { SlidingWindowLimiter } from '../../src/limiter.ts';

class Clock {
  now = 0;
  clock = () => this.now;
}

test('allows up to the maximum then rejects', () => {
  const limiter = new SlidingWindowLimiter(2, 1000, new Clock().clock);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), true);
  assert.equal(limiter.allow(), false);
});

test('invalid constructor arguments throw', () => {
  const clock = new Clock().clock;
  assert.throws(() => new SlidingWindowLimiter(0, 1000, clock), RangeError);
  assert.throws(() => new SlidingWindowLimiter(1, 0, clock), RangeError);
});
