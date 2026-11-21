// Expected slugs follow NFKD decomposition and mark removal.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { foldText } from '../../src/normalize.ts';
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

test('spec basic examples', () => {
  assert.equal(slugify('Hello World'), 'hello-world');
  assert.equal(slugify('  A.B.C  '), 'a-b-c');
  assert.equal(slugify('a__b'), 'a-b');
});

test('NFKD compatibility decomposition folds non-ASCII forms', () => {
  // spec.md: NFKD decomposes circled digits and ligatures before mark removal.
  assert.equal(slugify('①'), '1');    // U+2460 CIRCLED DIGIT ONE
  assert.equal(slugify('ﬁ'), 'fi');   // U+FB01 LATIN SMALL LIGATURE FI
  assert.equal(slugify('Ångström'), 'angstrom');
});

test('foldText exposes the documented NFKD + mark-strip + lowercase result', () => {
  assert.equal(foldText('Café'), 'cafe');
  assert.equal(foldText('À'), 'a');
});

test('separator-only input is empty and digits are kept', () => {
  // spec.md: empty result when no ASCII alphanumerics; [a-z0-9] includes digits.
  assert.equal(slugify('---'), '');
  assert.equal(slugify('   '), '');
  assert.equal(slugify('123'), '123');
});
