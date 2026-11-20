// Visible values contain no control characters and no surrounding whitespace.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { sanitizeHeaderValue, isSafeHeaderValue, buildHeader } from '../../src/headers.ts';

test('plain value is unchanged', () => {
  assert.equal(sanitizeHeaderValue('hello'), 'hello');
  assert.equal(isSafeHeaderValue('hello'), true);
});

test('builds a header line', () => {
  assert.equal(buildHeader('X-Test', 'ok'), 'X-Test: ok\r\n');
});

test('non-string value throws TypeError', () => {
  assert.throws(() => sanitizeHeaderValue(7 as unknown as string), TypeError);
});
