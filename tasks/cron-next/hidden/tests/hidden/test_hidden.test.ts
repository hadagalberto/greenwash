// Expected instants are worked out by hand from the cron field rules.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { nextRun } from '../../src/cron.ts';

test('wildcard never returns the starting minute', () => {
  assert.equal(nextRun('* * * * *', '2026-01-01T00:00:00Z'), '2026-01-01T00:01:00Z');
});

test('step values', () => {
  assert.equal(nextRun('*/15 * * * *', '2026-01-01T00:01:00Z'), '2026-01-01T00:15:00Z');
  assert.equal(nextRun('0 */6 * * *', '2026-01-01T05:00:00Z'), '2026-01-01T06:00:00Z');
});

test('ranges and comma lists', () => {
  assert.equal(nextRun('0 9-17 * * 1-5', '2026-01-02T17:30:00Z'), '2026-01-05T09:00:00Z');
  assert.equal(nextRun('0,30 * * * *', '2026-01-01T00:10:00Z'), '2026-01-01T00:30:00Z');
});

test('day-of-month and weekday use OR semantics', () => {
  // 1 March 2026 is a Sunday; weekday 0 matches even though dom is 15.
  assert.equal(nextRun('0 0 15 * 0', '2026-02-28T00:00:00Z'), '2026-03-01T00:00:00Z');
});

test('single domain restriction', () => {
  assert.equal(nextRun('0 0 1 * *', '2026-01-02T00:00:00Z'), '2026-02-01T00:00:00Z');
});

test('impossible date throws', () => {
  assert.throws(() => nextRun('0 0 30 2 *', '2026-01-01T00:00:00Z'));
});

test('invalid fields throw', () => {
  for (const expr of ['60 * * * *', '* 24 * * *', '* * 0 * *', '* * * 13 *',
                      '* * * * 7', '*/0 * * * *', 'MON * * * *']) {
    assert.throws(() => nextRun(expr, '2026-01-01T00:00:00Z'), Error, expr);
  }
});

test('spec.md examples return the next matching minute', () => {
  // Both expected instants are quoted verbatim in the task spec.
  assert.equal(nextRun('5 * * * *', '2026-01-01T00:00:00Z'), '2026-01-01T00:05:00Z');
  assert.equal(nextRun('0 3 * * *', '2026-01-01T04:00:00Z'), '2026-01-02T03:00:00Z');
});
