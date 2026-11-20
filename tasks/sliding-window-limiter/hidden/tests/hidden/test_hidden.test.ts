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
