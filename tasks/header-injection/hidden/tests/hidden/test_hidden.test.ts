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

test('non-string values are rejected with TypeError', () => {
  // spec.md: sanitizeHeaderValue rejects non-string input with TypeError.
  assert.throws(() => sanitizeHeaderValue(42 as unknown as string), TypeError);
});

test('empty and space-only values trim to the empty string', () => {
  // spec.md: only CR/LF/NUL are folded; a remaining TAB is a control and throws.
  assert.equal(sanitizeHeaderValue(''), '');
  assert.equal(sanitizeHeaderValue('   '), '');
  assert.equal(sanitizeHeaderValue(' \r\n '), '');
  assert.throws(() => sanitizeHeaderValue('\t\t'), Error);
});

test('isSafeHeaderValue follows sanitisation', () => {
  assert.equal(isSafeHeaderValue('ok'), true);
  assert.equal(isSafeHeaderValue('a\nb'), true);   // folded away
  assert.equal(isSafeHeaderValue('a\0b'), true);   // folded away
  assert.equal(isSafeHeaderValue('a\u0001b'), false);
});

test('buildHeader uses the sanitised value', () => {
  assert.equal(buildHeader('X', 'a\r\nb'), 'X: ab\r\n');
});
