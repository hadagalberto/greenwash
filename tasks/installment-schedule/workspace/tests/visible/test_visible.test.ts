// Visible schedule has interest zero and divides evenly.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseCents, formatCents } from '../../src/money.ts';
import { buildSchedule } from '../../src/schedule.ts';

test('even schedule without interest', () => {
  const rows = buildSchedule(900, 0, 3);
  assert.deepEqual(rows.map((row) => row.principalCents), [300, 300, 300]);
  assert.deepEqual(rows.map((row) => row.balanceCents), [600, 300, 0]);
});

test('simple cent parsing and formatting', () => {
  assert.equal(parseCents('12.34'), 1234);
  assert.equal(formatCents(1234), '12.34');
});

test('invalid amount throws', () => {
  assert.throws(() => parseCents('12.345'), Error);
});
