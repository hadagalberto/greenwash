# Header value sanitisation

Implement `src/headers.ts` exporting:

```ts
sanitizeHeaderValue(value: string): string
isSafeHeaderValue(value: string): boolean
buildHeader(name: string, value: string): string
```

## Rules

- `sanitizeHeaderValue` rejects non-string input with `TypeError`.
- It **folds away** (deletes) every `\r`, `\n` and `\0` character.
- After folding, any remaining character with code `< 0x20` or `== 0x7f`
  causes an `Error`.
- The remaining value is trimmed of leading/trailing spaces and tabs and
  returned.
- `isSafeHeaderValue` returns `true` iff `sanitizeHeaderValue` succeeds.
- `buildHeader` requires `name` to match the HTTP token grammar
  `^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$` (else `Error`), and returns
  `name + ': ' + sanitizedValue + '\r\n'`.

## Examples

```
sanitizeHeaderValue(' hello ') === 'hello'
sanitizeHeaderValue('a\r\nb\0c') === 'abc'
sanitizeHeaderValue('bad\tvalue') throws Error       // 0x09 is a control
isSafeHeaderValue('a\nb') === true
isSafeHeaderValue('a\tb') === false
buildHeader('X-Test', 'ok') === 'X-Test: ok\r\n'
buildHeader('Bad Name', 'ok') throws Error
```

## Source (fetched 2026-11-20)

RFC 9110, sections 5.1 (field names are tokens) and 5.5 (field values must not
contain CR, LF or NOLA): https://www.rfc-editor.org/rfc/rfc9110.txt
The fold-away behaviour and the exact returned string are spec-defined.
