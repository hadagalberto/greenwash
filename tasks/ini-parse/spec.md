# INI parser

Implement `parse_ini(text: str) -> dict[str, dict[str, str]]` in
`src/ini_parse.py`.

## Rules

- A line whose first non-space character is `;` or `#` is a comment and is
  ignored. Blank lines are ignored.
- A section header is `[name]`; `name` is trimmed and must be non-empty.
  Repeated headers for the same name **merge** into one section (later keys
  override earlier ones).
- A key/value line uses the first `=` if present, otherwise the first `:`.
  Both key and value are trimmed. Empty values are allowed. An empty key is
  invalid.
- An inline comment starts at the first `;` or `#` that is either at index 0
  of the value or preceded by whitespace, unless that character is inside
  single or double quotes. Everything from there is removed and the remaining
  value is right-trimmed.
- If the trimmed value starts and ends with the same quote character (`'` or
  `"`), exactly one pair of quotes is removed; no escape processing occurs.
- A line that begins with whitespace continues the previous key's value:
  append one space then the processed continuation text. If the continuation
  is empty, nothing is appended.
- Keys before any section go into the section keyed by the empty string `''`.
- A line that is neither a section, a key/value pair, a comment nor a
  continuation raises `ValueError`. Non-string input raises `TypeError`.

## Examples

```
parse_ini('[a]\nx = 1\ny: "two words"\n')
  == {'a': {'x': '1', 'y': 'two words'}}

parse_ini('top = yes\n[a]\nk = first\n    second\n[a]\nk = last ; note\n')
  == {'': {'top': 'yes'}, 'a': {'k': 'last'}}
```

## Source (fetched 2026-11-20)

Wikipedia, "INI file": files are divided into sections introduced by `[name]`,
with `name=value` (or `name: value`) entries and `;`/`#` comments:
https://en.wikipedia.org/wiki/INI_file
The exact inline-comment, quote and continuation rules above are spec-defined.
