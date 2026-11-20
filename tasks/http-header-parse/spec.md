# Parse comma-separated HTTP field values

Implement `src/headers.ts` exporting exactly:

```ts
export function parseHeaderValue(value: string): string[]
```

`value` is the combined value of an HTTP field whose grammar is a
comma-separated list of tokens and/or quoted strings (for example
`Accept`, `Cache-Control`, `Vary`, `If-None-Match`). Split it into its
individual elements using the HTTP field-value grammar.

## Rules

1. Split `value` on every comma (`,`) that is **outside** a quoted-string.
2. A quoted-string starts with a double quote (`"`) and ends with the next
   unescaped double quote. Inside a quoted-string, a backslash (`\`) begins a
   **quoted-pair**: the backslash is discarded and the following character is
   taken literally, whatever it is (including `,` and `"`). A comma inside a
   quoted-string is data, not a delimiter.
3. For an **unquoted** element, strip optional leading and trailing SP (`U+0020`)
   and HTAB (`U+0009`) — RFC 9110 OWS. No other character is trimmed.
4. For a **quoted** element, remove the surrounding quotes and unescape every
   quoted-pair. Do **not** trim whitespace from the resulting content: spaces
   inside the quotes are data. OWS after the closing quote is ignored.
5. Skip empty unquoted elements: elements that contain only OWS after trimming
   produce no entry. A quoted element is always kept, even `""`, which produces
   the empty string entry `""`.
6. Throw an `Error` if a quoted-string is not terminated, if a quoted-string
   ends with a dangling backslash (a backslash with no following character), or
   if a double quote appears in an unquoted element (for example `a"b`) or
   after the closing quote of a quoted element (for example `"a"b`).
7. Outside a quoted-string a backslash is an ordinary data character (quoted
   pairs exist only inside quoted-strings).
8. Return `[]` for empty input or input containing only OWS.

## Examples (all are exact expectations)

| input | result |
| --- | --- |
| `"a, b"` | `["a", "b"]` |
| `'"a,b", c'` | `["a,b", "c"]` |
| `'"a\\"b", c'` | `['a"b', "c"]` |
| `"a,,b"` | `["a", "b"]` |
| `'  "x y" , z'` | `["x y", "z"]` |
| `'"a\\,b", c'` | `["a,b", "c"]` |
| `'  "  "  '` | `["  "]` |
| `'""'` | `[""]` |
| `"   \t "` | `[]` |
| `'"unterminated'` | throws `Error` |
| `'"trailing\\'` | throws `Error` |
| `'a"b'` | throws `Error` |

The table uses JavaScript/TypeScript string-literal notation: `'"a\\"b", c'`
is the eight-character-plus input `"a\"b", c` on the wire.

## Sources (fetched 2026-11-20)

- https://www.rfc-editor.org/rfc/rfc9110.txt
  - Section 5.5 "Field Values": leading/trailing whitespace is not part of a
    field value; OWS is SP/HTAB.
  - Section 5.6.1 "Lists (#rule ABNF Extension)": list syntax uses commas as
    element delimiters.
  - Section 5.6.2 "Tokens": double quote and comma are delimiters, so a value
    containing them must be a quoted-string.
  - Section 5.6.4 "Quoted Strings": `quoted-string = DQUOTE *( qdtext /
    quoted-pair ) DQUOTE`, `quoted-pair = "\" ( HTAB / SP / VCHAR / obs-text )`.
    Recipients MUST handle a quoted-pair "as if it were replaced by the octet
    following the backslash".
