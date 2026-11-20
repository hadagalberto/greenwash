// Visible expressions have unrestricted day fields.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { nextRun } from '../../src/cron.ts';

test('next matching minute', () => {
  assert.equal(nextRun('5 * * * *', '2026-01-01T00:00:00Z'), '2026-01-01T00:05:00Z');
});

test('next matching hour', () => {
  assert.equal(nextRun('0 3 * * *', '2026-01-01T04:00:00Z'), '2026-01-02T03:00:00Z');
});

test('too few fields throw', () => {
  assert.throws(() => nextRun('* * *', '2026-01-01T00:00:00Z'));
});
