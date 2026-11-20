# CSV parser (RFC 4180-style)

Implement `src/csv.ts` exporting:

```ts
export function parseCsv(text: string): string[][];
```

The grammar follows RFC 4180 section 2 (rules 2, 4, 5, 6 and 7 and the ABNF
in that section), fetched 2026-11-20:
https://www.rfc-editor.org/rfc/rfc4180.txt

## Rules

- A comma (`,`) separates fields within a record. Every comma terminates the
  current field, and the field that follows it may be empty: `parseCsv("a,")`
  returns `[["a",""]]`. (RFC 4180 rule 4 discourages a trailing comma in valid
  RFC files; this task deliberately defines its result instead of rejecting it.)
- Records are separated by `CRLF` (`\r\n`) or by a bare `LF` (`\n`). RFC 4180
  uses CRLF; this task also accepts bare LF. A record separator is never part
  of a field.
- A field may be enclosed in double quotes. A quoted field may contain commas,
  line breaks and doubled quotes. Inside a quoted field, two consecutive double
  quotes (`""`) represent one literal double quote.
- A quote character that begins a field must be the first character of that
  field. Spaces are ordinary characters: fields are **never trimmed**.
- A trailing record terminator does not create an extra empty record.
- Empty input returns `[]`.
- An unterminated quoted field is an error: throw an `Error`.

## Vectors

| input | result |
| --- | --- |
| `"a,b\n1,2"` | `[["a","b"],["1","2"]]` |
| `'a,"b,c"\n'` | `[["a","b,c"]]` |
| `'"he said ""hi""",x'` | `[["he said \"hi\"","x"]]` |
| `'"line1\nline2",z'` | `[["line1\nline2","z"]]` |
| `"a,b\r\n1,2\r\n"` | `[["a","b"],["1","2"]]` |
| `""` (empty input) | `[]` |
| `"a,,c"` | `[["a","","c"]]` |
| `'""'` | `[[""]]` |
| `"a,"` | `[["a",""]]` (trailing empty field) |

Additional examples:

```ts
parseCsv('"",x');        // [["", "x"]]
parseCsv(" a , b ");     // [[" a ", " b "]]  (no trimming)
parseCsv("a,b\n");       // [["a", "b"]]      (no extra record)
parseCsv('"x\r\ny",z');  // [["x\r\ny", "z"]] (CRLF kept inside quotes)
parseCsv('"oops');       // throws Error
```
