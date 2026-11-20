// Vectors are the RFC 6902 Appendix A examples plus pointer edge cases.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { applyPatch } from '../../src/patch.ts';
import { parsePointer } from '../../src/pointer.ts';

test('tilde unescape order (RFC 6901 section 4)', () => {
  assert.deepEqual(parsePointer('/~01'), ['~1']);
  assert.deepEqual(parsePointer('/a~1b'), ['a/b']);
  assert.throws(() => parsePointer('/~2'), Error);
  const doc = { '/': 9, '~1': 10 };
  assert.deepEqual(applyPatch(doc, [{ op: 'test', path: '/~01', value: 10 }]), doc);
  assert.throws(() => applyPatch(doc, [{ op: 'test', path: '/~01', value: '10' }]), Error);
});

test('move an array element (RFC A.7)', () => {
  assert.deepEqual(
    applyPatch({ foo: ['all', 'grass', 'cows', 'eat'] },
               [{ op: 'move', from: '/foo/1', path: '/foo/3' }]),
    { foo: ['all', 'cows', 'eat', 'grass'] });
});

test('move an object member (RFC A.6)', () => {
  const doc = { foo: { bar: 'baz', waldo: 'fred' }, qux: { corge: 'grault' } };
  assert.deepEqual(applyPatch(doc, [{ op: 'move', from: '/foo/waldo', path: '/qux/thud' }]),
                   { foo: { bar: 'baz' }, qux: { corge: 'grault', thud: 'fred' } });
});

test('copy is deep and independent', () => {
  const doc = { a: { n: 1 }, b: null };
  const out = applyPatch(doc, [{ op: 'copy', from: '/a', path: '/b' }]) as {
    a: { n: number }; b: { n: number };
  };
  assert.deepEqual(out, { a: { n: 1 }, b: { n: 1 } });
  out.b.n = 9;
  assert.equal(out.a.n, 1);
});

test('add to a nonexistent parent fails (RFC A.12)', () => {
  assert.throws(() => applyPatch({ foo: 'bar' }, [{ op: 'add', path: '/baz/bat', value: 'qux' }]),
                Error);
});

test('append with dash and ignore extra members (RFC A.11, A.16)', () => {
  assert.deepEqual(applyPatch({ foo: ['bar'] },
                              [{ op: 'add', path: '/foo/-', value: ['abc', 'def'], xyz: 1 }]),
                   { foo: ['bar', ['abc', 'def']] });
});

test('failed test aborts the whole patch', () => {
  const doc = { a: 1 };
  assert.throws(() => applyPatch(doc, [
    { op: 'replace', path: '/a', value: 2 },
    { op: 'test', path: '/a', value: 1 },
  ]), Error);
  assert.deepEqual(doc, { a: 1 });
});

test('root replacement and leading zeros rejected', () => {
  assert.deepEqual(applyPatch({ a: 1 }, [{ op: 'add', path: '', value: [9] }]), [9]);
  assert.throws(() => applyPatch([1, 2], [{ op: 'remove', path: '/01' }]), Error);
});

test('move into own child fails', () => {
  assert.throws(() => applyPatch({ a: { b: 1 } }, [{ op: 'move', from: '/a', path: '/a/b' }]), Error);
});
