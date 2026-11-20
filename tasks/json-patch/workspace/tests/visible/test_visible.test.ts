// Visible cases use simple object/array paths only.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { applyPatch } from '../../src/patch.ts';

test('add an object member', () => {
  assert.deepEqual(applyPatch({ foo: 'bar' }, [{ op: 'add', path: '/baz', value: 'qux' }]),
                   { foo: 'bar', baz: 'qux' });
});

test('add into an array', () => {
  assert.deepEqual(applyPatch({ foo: ['bar', 'baz'] },
                              [{ op: 'add', path: '/foo/1', value: 'qux' }]),
                   { foo: ['bar', 'qux', 'baz'] });
});

test('remove and replace', () => {
  assert.deepEqual(applyPatch({ baz: 'qux', foo: 'bar' }, [{ op: 'remove', path: '/baz' }]),
                   { foo: 'bar' });
  assert.deepEqual(applyPatch({ baz: 'qux' }, [{ op: 'replace', path: '/baz', value: 'boo' }]),
                   { baz: 'boo' });
});

test('unknown operation throws', () => {
  assert.throws(() => applyPatch({}, [{ op: 'nope', path: '/x' }]), Error);
});
