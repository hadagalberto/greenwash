// HTTP-date and numeric edge vectors.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseRetryAfter } from '../../src/retry_after.ts';

test('invalid weekday is rejected', () => {
  assert.throws(() => parseRetryAfter('Mon, 06 Nov 1994 08:49:37 GMT', 0), Error);
});

test('obsolete and asctime date formats are rejected', () => {
  assert.throws(() => parseRetryAfter('Sunday, 06-Nov-94 08:49:37 GMT', 0), Error);
  assert.throws(() => parseRetryAfter('Sun Nov  6 08:49:37 1994', 0), Error);
});

test('numeric validation', () => {
  assert.equal(parseRetryAfter(' 10 ', 5000), 15000);
  assert.throws(() => parseRetryAfter('-2', 0), Error);
  assert.throws(() => parseRetryAfter('1.5', 0), Error);
  assert.throws(() => parseRetryAfter('', 0), Error);
  assert.equal(parseRetryAfter('0', 999), 999);
});

test('nowMs must be finite', () => {
  assert.throws(() => parseRetryAfter('1', Number.NaN), Error);
  assert.throws(() => parseRetryAfter('1', Number.POSITIVE_INFINITY), Error);
});

test('date value ignores nowMs', () => {
  const date = 'Wed, 21 Oct 2015 07:28:00 GMT';
  assert.equal(parseRetryAfter(date, 0), parseRetryAfter(date, 123456789));
});

test('spec examples for seconds and IMF-fixdate', () => {
  // Both expected values are quoted verbatim in the task spec.
  assert.equal(parseRetryAfter('2', 0), 2000);
  assert.equal(parseRetryAfter('Sun, 06 Nov 1994 08:49:37 GMT', 0), 784111777000);
});

test('non-string header throws', () => {
  assert.throws(() => parseRetryAfter(42 as unknown as string, 0), Error);
});

test('impossible date is rejected by the canonical round-trip check', () => {
  assert.throws(() => parseRetryAfter('Sun, 32 Nov 1994 08:49:37 GMT', 0), Error);
});
