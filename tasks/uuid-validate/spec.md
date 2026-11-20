# UUID validation

Implement `is_valid_uuid(text: object, version: int | None = None) -> bool`
in `src/uuid_validate.py`. Return a bool; never raise for malformed input.

## Rules (RFC 4122)

- The string must match exactly `8-4-4-4-12` hexadecimal digits with hyphens
  at those positions. Hex digits are case-insensitive. No braces, no
  `urn:uuid:` prefix, no short/long forms, no whitespace.
- The variant bits are the two most significant bits of octet 8. In the string
  this is the first hex digit of the fourth group; RFC 4122's variant is `10xx`,
  so that digit must be `8`, `9`, `a` or `b` (case-insensitive).
- The version is the four most significant bits of `time_hi_and_version`, i.e.
  the first hex digit of the third group. It must be `1`, `2`, `3`, `4` or `5`.
- If `version` is supplied it must be an `int` (not `bool`) in `1..5`, and the
  UUID's version must equal it; otherwise return `False`.
- The all-zero UUID fails the variant test and is therefore invalid.

## Examples

```
is_valid_uuid('f81d4fae-7dec-11d0-a765-00a0c91e6bf6') is True       # v1, RFC example
is_valid_uuid('550e8400-e29b-41d4-a716-446655440000') is True       # v4
is_valid_uuid('550e8400-e29b-41d4-a716-446655440000', 1) is False
is_valid_uuid('550e8400-e29b-41d4-a716-446655440000', 4) is True
is_valid_uuid('550e8400e29b41d4a716446655440000') is False
is_valid_uuid('{550e8400-e29b-41d4-a716-446655440000}') is False
is_valid_uuid('550e8400-e29b-41d4-c716-446655440000') is False      # wrong variant
is_valid_uuid('00000000-0000-0000-0000-000000000000') is False
```

## Source (fetched 2026-11-20)

RFC 4122, sections 4.1.1 (variant: `Msb0=1, Msb1=0`), 4.1.3 (versions 1-5) and
section 3 (the `8-4-4-4-12` string representation, hex case-insensitive):
https://www.rfc-editor.org/rfc/rfc4122.txt
