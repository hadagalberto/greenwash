// RFC 6902 JSON Patch application over a cloned document.
import type { Json } from './pointer.ts';
import { addAt, parsePointer, readAt, removeAt } from './pointer.ts';

function deepEqual(left: Json, right: Json): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right)) {
    if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) return false;
    return left.every((item, index) => deepEqual(item, right[index]));
  }
  if (left !== null && right !== null && typeof left === 'object' && typeof right === 'object') {
    const keys = Object.keys(left);
    if (keys.length !== Object.keys(right).length) return false;
    return keys.every((key) =>
      Object.prototype.hasOwnProperty.call(right, key) && deepEqual(left[key], right[key]));
  }
  return false;
}

function requireValue(op: { value?: Json }): Json {
  if (!Object.prototype.hasOwnProperty.call(op, 'value')) throw new Error('missing value');
  return op.value as Json;
}

export function applyPatch(document: Json, operations: Json): Json {
  if (!Array.isArray(operations)) throw new Error('patch must be an array');
  let result: Json = structuredClone(document);
  for (const operation of operations) {
    if (operation === null || typeof operation !== 'object' || Array.isArray(operation)) {
      throw new Error('bad operation');
    }
    const op = operation as { [key: string]: Json };
    const path = op['path'];
    if (typeof path !== 'string') throw new Error('missing path');
    const tokens = parsePointer(path);
    switch (op['op']) {
      case 'add':
        result = addAt(result, tokens, requireValue(op));
        break;
      case 'remove':
        void tokens;
        break;
      case 'replace': {
        const value = requireValue(op);
        removeAt(result, tokens);
        result = addAt(result, tokens, value);
        break;
      }
      case 'move': {
        if (typeof op['from'] !== 'string') throw new Error('missing from');
        const from = parsePointer(op['from']);
        if (from.length < tokens.length && from.every((token, index) => token === tokens[index])) {
          throw new Error('cannot move into own child');
        }
        const value = structuredClone(readAt(result, from));
        removeAt(result, from);
        result = addAt(result, tokens, value);
        break;
      }
      case 'copy': {
        if (typeof op['from'] !== 'string') throw new Error('missing from');
        const value = structuredClone(readAt(result, parsePointer(op['from'])));
        result = addAt(result, tokens, value);
        break;
      }
      case 'test':
        if (!deepEqual(readAt(result, tokens), requireValue(op))) throw new Error('test failed');
        break;
      default:
        throw new Error('unknown operation');
    }
  }
  return result;
}
