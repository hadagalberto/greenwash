// Visible cases never overflow and use only a single element for shift.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { RingBuffer } from '../../src/ring.ts';

test('push then shift one element', () => {
  const b = new RingBuffer<string>(3);
  assert.equal(b.push('a'), undefined);
  assert.equal(b.shift(), 'a');
  assert.equal(b.size, 0);
});

test('fills up to capacity', () => {
  const b = new RingBuffer<number>(3);
  b.push(1); b.push(2); b.push(3);
  assert.equal(b.size, 3);
  assert.equal(b.isFull, true);
});

test('invalid capacity throws', () => {
  assert.throws(() => new RingBuffer(0), RangeError);
  assert.throws(() => new RingBuffer(1.5), RangeError);
});
