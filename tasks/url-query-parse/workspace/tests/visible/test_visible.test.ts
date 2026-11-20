// Visible queries are plain ASCII without repeats or escapes.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseQuery } from '../../src/query.ts';

test('simple pairs', () => {
  assert.deepEqual(parseQuery('a=1&b=2'), { a: '1', b: '2' });
});

test('leading question mark is ignored', () => {
  assert.deepEqual(parseQuery('?x=9'), { x: '9' });
});

test('missing value is empty string', () => {
  assert.deepEqual(parseQuery('flag'), { flag: '' });
});
