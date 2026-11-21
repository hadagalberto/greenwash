// Expected decoded strings are written by hand from RFC 3986 percent rules.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseQuery } from '../../src/query.ts';

test('repeated keys keep order', () => {
  assert.deepEqual(parseQuery('?a=1&a=2&a=3'), { a: ['1', '2', '3'] });
});

test('plus and percent decoding', () => {
  assert.deepEqual(parseQuery('name=Hello+World'), { name: 'Hello World' });
  assert.deepEqual(parseQuery('x=%2B%20%C3%A9'), { x: '+ é' });
  assert.deepEqual(parseQuery('%41=%42'), { A: 'B' });
});

test('encoded ampersand and equals stay in the value', () => {
  assert.deepEqual(parseQuery('q=a%3Db%26c'), { q: 'a=b&c' });
});

test('empty segments and empty keys', () => {
  assert.deepEqual(parseQuery('a=1&&=x&'), { a: '1', '': 'x' });
  assert.deepEqual(parseQuery('a=1&a=&a=3'), { a: ['1', '', '3'] });
});

test('malformed escapes throw', () => {
  for (const query of ['bad=%ZZ', 'bad=%2', 'bad=%']) {
    assert.throws(() => parseQuery(query), Error, query);
  }
});

test('invalid utf-8 throws', () => {
  assert.throws(() => parseQuery('bad=%FF'), Error);
});

test('spec examples', () => {
  // Expectations are quoted verbatim in the task spec.
  assert.deepEqual(parseQuery('a=1&b=2'), { a: '1', b: '2' });
  assert.deepEqual(parseQuery('flag&empty='), { flag: '', empty: '' });
  assert.throws(() => parseQuery('bad=%ZZ'), Error);
});

test('leading question mark is optional and empty segments are skipped', () => {
  assert.deepEqual(parseQuery(''), {});
  assert.deepEqual(parseQuery('?'), {});
  assert.deepEqual(parseQuery('?a=1'), { a: '1' });
  assert.deepEqual(parseQuery('&&a=1&&'), { a: '1' });
});
