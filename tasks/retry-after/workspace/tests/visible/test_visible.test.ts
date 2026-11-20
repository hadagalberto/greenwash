// Visible cases use numeric seconds and one canonical IMF-fixdate.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseRetryAfter } from '../../src/retry_after.ts';

test('numeric seconds become an absolute time', () => {
  assert.equal(parseRetryAfter('2', 0), 2000);
  assert.equal(parseRetryAfter('10', 5000), 15000);
});

test('canonical HTTP date', () => {
  assert.equal(parseRetryAfter('Sun, 06 Nov 1994 08:49:37 GMT', 0), 784111777000);
});

test('junk throws', () => {
  assert.throws(() => parseRetryAfter('not-a-date', 0), Error);
});
