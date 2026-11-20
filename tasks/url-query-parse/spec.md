# Query string parser

Implement `parseQuery(query: string): Record<string, string | string[]>`
in `src/query.ts`.

## Rules

- A leading `?` is optional and ignored. Split the rest on `&`; empty segments
  are skipped.
- Split each segment at the **first** `=`. Without `=`, the value is `''`.
- Decode keys and values identically: `+` becomes a space; `%HH` becomes the
  byte `0xHH`; all resulting bytes are decoded as strict UTF-8. A malformed
  escape (`%` not followed by two hex digits) or invalid UTF-8 throws `Error`.
- Repeated keys produce an array of values in encounter order. A key seen once
  maps to a plain string. Keys with no value map to `''`.
- Empty keys are allowed.

## Examples

```
parseQuery('a=1&b=2')           === { a: '1', b: '2' }
parseQuery('?a=1&a=2&a=3')      === { a: ['1', '2', '3'] }
parseQuery('name=Hello+World')  === { name: 'Hello World' }
parseQuery('x=%2B%20%C3%A9')    === { x: '+ é' }
parseQuery('flag&empty=')       === { flag: '', empty: '' }
parseQuery('bad=%ZZ')           throws Error
```

## Source (fetched 2026-11-20)

RFC 3986, section 2.1: percent-encoding represents a byte as `%` followed by
two hexadecimal digits; UTF-8 is the expected encoding for new URI schemes:
https://www.rfc-editor.org/rfc/rfc3986.txt
The `+`-as-space rule follows HTML form encoding and is spec-defined here.
