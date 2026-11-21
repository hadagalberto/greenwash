// JSON Pointer (RFC 6901) helpers for JSON Patch.
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export function parsePointer(pointer: string): string[] {
  if (pointer === '') return [];
  if (!pointer.startsWith('/')) throw new Error('bad pointer');
  if (/~(?![01])/.test(pointer)) throw new Error('bad escape');
  return pointer.slice(1).split('/').map((token) => token.replace(/~1/g, '/').replace(/~0/g, '~'));
}

function arrayIndex(token: string, length: number, append: boolean): number {
  if (token === '-' && append) return length;
  if (!/^(0|[1-9]\d*)$/.test(token)) throw new Error('bad array index');
  const index = Number(token);
  if (index > length) throw new Error('array index out of range');
  return index;
}

export function readAt(doc: Json, tokens: string[]): Json {
  let current = doc;
  for (const token of tokens) {
    if (Array.isArray(current)) {
      current = current[arrayIndex(token, current.length, false)];
    } else if (current !== null && typeof current === 'object') {
      if (!Object.prototype.hasOwnProperty.call(current, token)) throw new Error('missing member');
      current = current[token];
    } else {
      throw new Error('pointer into primitive');
    }
  }
  return current;
}

export function parentAt(doc: Json, tokens: string[]): { parent: Json; key: string } {
  if (tokens.length === 0) throw new Error('root has no parent');
  const parent = readAt(doc, tokens.slice(0, -1));
  return { parent, key: tokens[tokens.length - 1] };
}

export function addAt(doc: Json, tokens: string[], value: Json): Json {
  if (tokens.length === 0) return value;
  const { parent, key } = parentAt(doc, tokens);
  if (Array.isArray(parent)) {
    parent.splice(arrayIndex(key, parent.length, true), 0, value);
  } else if (parent !== null && typeof parent === 'object') {
    parent[key] = value;
  } else {
    throw new Error('add into primitive');
  }
  return doc;
}

export function removeAt(doc: Json, tokens: string[]): Json {
  const { parent, key } = parentAt(doc, tokens);
  if (Array.isArray(parent)) {
    parent.splice(arrayIndex(key, parent.length, false), 1);
  } else if (parent !== null && typeof parent === 'object') {
    if (!Object.prototype.hasOwnProperty.call(parent, key)) throw new Error('missing member');
    delete parent[key];
  } else {
    throw new Error('remove from primitive');
  }
  return doc;
}
