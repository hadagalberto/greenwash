// Wrap-around, eviction and ordering vectors.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { RingBuffer } from '../../src/ring.ts';

test('logical order survives wrap-around', () => {
  const b = new RingBuffer<number>(3);
  b.push(1); b.push(2); b.push(3);
  assert.equal(b.push(4), 1);
  assert.deepEqual(b.toArray(), [2, 3, 4]);
  assert.equal(b.push(5), 2);
  assert.deepEqual(b.toArray(), [3, 4, 5]);
});

test('shift after wrap returns oldest', () => {
  const b = new RingBuffer<string>(2);
  b.push('a'); b.push('b');
  assert.equal(b.push('c'), 'a');
  assert.equal(b.shift(), 'b');
  assert.equal(b.shift(), 'c');
  assert.equal(b.shift(), undefined);
  assert.equal(b.size, 0);
  assert.equal(b.isFull, false);
});

test('clear resets positions', () => {
  const b = new RingBuffer<number>(2);
  b.push(1); b.push(2);
  assert.equal(b.push(3), 1);
  b.clear();
  assert.deepEqual(b.toArray(), []);
  b.push(9); b.push(10);
  assert.equal(b.push(11), 9);
  assert.deepEqual(b.toArray(), [10, 11]);
});

test('capacity boundary is exact', () => {
  const b = new RingBuffer<number>(1);
  assert.equal(b.push(1), undefined);
  assert.equal(b.isFull, true);
  assert.equal(b.push(2), 1);
  assert.deepEqual(b.toArray(), [2]);
});
