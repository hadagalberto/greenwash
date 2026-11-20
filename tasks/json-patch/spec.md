# JSON Patch

Implement `src/pointer.ts` and `src/patch.ts`.

## `src/pointer.ts`

- `parsePointer(pointer: string): string[]`: `''` means the root; otherwise
  the pointer must start with `/`. Split on `/`, then unescape `~1` to `/`
  **first** and `~0` to `~` second; any other `~` sequence throws `Error`.
- Helpers `readAt`, `addAt`, `removeAt` resolve JSON Pointer tokens against
  objects and arrays. Array tokens are unsigned decimal integers without
  leading zeros; `-` is allowed only for `add` and means append. Missing
  members/indices and out-of-range indices throw `Error`.

## `src/patch.ts`

`applyPatch(document: Json, operations: Json): Json` deep-clones the document
and applies operations in order, returning the result. Support:

- `add` (object member or array insertion, replacing an existing member),
- `remove` (target must exist),
- `replace` (target must exist),
- `move` (`from` must exist; `from` must not be a proper prefix of `path`),
- `copy` (deep-copied value),
- `test` (structural equality, type-sensitive).

Unknown `op`, missing required members, failed `test`, or an unsuccessful
operation throw `Error`. Undefined extra members are ignored. An error aborts
the whole patch; the caller's document is never mutated.

## Examples (RFC 6902 Appendix A)

```
applyPatch({ foo: ['bar', 'baz'] },
            [{ op: 'add', path: '/foo/1', value: 'qux' }])
  === { foo: ['bar', 'qux', 'baz'] }

applyPatch({ foo: ['all', 'grass', 'cows', 'eat'] },
            [{ op: 'move', from: '/foo/1', path: '/foo/3' }])
  === { foo: ['all', 'cows', 'eat', 'grass'] }

applyPatch({ '/': 9, '~1': 10 },
            [{ op: 'test', path: '/~01', value: 10 }])  // succeeds
applyPatch({ '/': 9, '~1': 10 },
            [{ op: 'test', path: '/~01', value: '10' }]) // throws (string vs number)
```

## Sources (fetched 2026-11-20)

RFC 6902, sections 4 and Appendix A: operation semantics and examples:
https://www.rfc-editor.org/rfc/rfc6902.txt
RFC 6901, sections 3-4: pointer syntax, `~1`/`~0` unescape ordering and array
index rules: https://www.rfc-editor.org/rfc/rfc6901.txt
