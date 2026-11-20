// Visible inputs are ASCII with spaces and dots.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { slugify } from '../../src/slug.ts';

test('spaces become dashes', () => {
  assert.equal(slugify('Hello World'), 'hello-world');
});

test('punctuation runs collapse', () => {
  assert.equal(slugify('  A.B.C  '), 'a-b-c');
});
