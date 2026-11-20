// Expected slugs follow NFKD decomposition and mark removal.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { slugify } from '../../src/slug.ts';

test('accented Latin letters are folded', () => {
  assert.equal(slugify('Café'), 'cafe');
  assert.equal(slugify('crème brûlée'), 'creme-brulee');
  assert.equal(slugify('Über'), 'uber');
});

test('separator runs and underscores', () => {
  assert.equal(slugify('a__b'), 'a-b');
  assert.equal(slugify('a---  b'), 'a-b');
  assert.equal(slugify('-start-end-'), 'start-end');
});

test('no ASCII alphanumerics gives empty string', () => {
  assert.equal(slugify('日本語'), '');
  assert.equal(slugify(''), '');
  assert.equal(slugify('!!!'), '');
});

test('non-string input throws', () => {
  assert.throws(() => slugify(42 as unknown as string), TypeError);
});
