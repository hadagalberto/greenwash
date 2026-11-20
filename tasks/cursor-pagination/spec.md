# Opaque pagination cursors

Implement `src/codec.py` and `src/pagination.py`.

## `src/codec.py`

- `encode_cursor(payload: dict) -> str`: serialize with `json.dumps` using
  `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`; UTF-8 encode;
  base64url encode; remove **all** `=` padding.
- `decode_cursor(token: str) -> dict`: accept only a non-empty ASCII string of
  unpadded base64url characters `[A-Za-z0-9_-]+`; reject `=` and any other
  character. Re-pad for decoding, decode UTF-8 strictly, parse JSON, and
  require the result to be an object. Any failure raises `ValueError`.

## `src/pagination.py`

- `paginate(items, offset, limit) -> (page, cursor)`: `offset` non-negative int,
  `limit` positive int (bools are invalid; `ValueError` otherwise). The page is
  `items[offset:offset+limit]`. Return `None` as the cursor when
  `offset + limit >= len(items)`, otherwise an encoded cursor
  `{'v': 1, 'offset': offset + limit}`.
- `decode_offset(token) -> int`: decode the cursor, require **exactly** the
  keys `v` and `offset`, `v == 1` (not `True`), and `offset` a non-negative
  integer (not `bool`). Any violation raises `ValueError`.

## Examples

```
items = [10, 20, 30, 40, 50]
page, token = paginate(items, 0, 2)   # page == [10, 20], token is a string
decode_offset(token) == 2
page2, token2 = paginate(items, 2, 2) # [30, 40], decode_offset(token2) == 4
page3, token3 = paginate(items, 4, 2) # [50], token3 is None
```

## Source (fetched 2026-11-20)

RFC 4648, section 5 "Base 64 Encoding with URL and Filename Safe Alphabet":
the URL-safe alphabet replaces `+`/`/` with `-`/`_` and padding may be omitted
when the decoder knows the data length: https://www.rfc-editor.org/rfc/rfc4648.txt
The cursor payload schema is spec-defined.
