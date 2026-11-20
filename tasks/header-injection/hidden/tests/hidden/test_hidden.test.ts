// Control-character and name-token vectors derived from RFC 9110.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { sanitizeHeaderValue, isSafeHeaderValue, buildHeader } from '../../src/headers.ts';

test('CR, LF and NUL are folded away', () => {
  assert.equal(sanitizeHeaderValue('a\r\nb\0c'), 'abc');
  assert.equal(sanitizeHeaderValue('x\r\ny'), 'xy');
});

test('other controls and DEL throw', () => {
  assert.throws(() => sanitizeHeaderValue('a\tb'), Error);
  assert.throws(() => sanitizeHeaderValue('a\u007fb'), Error);
  assert.throws(() => sanitizeHeaderValue('a\u0001b'), Error);
  assert.equal(isSafeHeaderValue('a\tb'), false);
  assert.equal(isSafeHeaderValue('a\nb'), true);
});

test('leading and trailing spaces and tabs are trimmed', () => {
  assert.equal(sanitizeHeaderValue('  hi  '), 'hi');
  assert.equal(buildHeader('X-A', '  hi  '), 'X-A: hi\r\n');
});

test('header names must be tokens', () => {
  for (const name of ['Bad Name', '', 'a:b', 'a\r\nb']) {
    assert.throws(() => buildHeader(name, 'ok'), Error, name);
  }
  assert.equal(buildHeader('X_1!', 'ok'), 'X_1!: ok\r\n');
});
