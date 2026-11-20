# Unicode canonical text handling

Implement three functions in `src/unicode_text.py`:

```py
def canonical_key(text: str) -> str: ...
def normalized_equal(left: str, right: str) -> bool: ...
def strip_marks(text: str) -> str: ...
```

## Exact rules

- `canonical_key` = `NFC(NFC(text).casefold())`. Normalize to NFC **before**
  casefolding (casefold can introduce decomposed sequences) and normalize
  again afterwards. Non-string input raises `TypeError`.
- `normalized_equal(a, b)` = `canonical_key(a) == canonical_key(b)`.
- `strip_marks` = `NDC`-style: normalize to `NFD`, drop every character whose
  Unicode general category starts with `M` (combining marks), then normalize
  back to `NFC`. Non-string input raises `TypeError`.
- No locale-specific or transliteration rules are applied.

## Examples

```
canonical_key('ABC') == 'abc'
normalized_equal('é', 'e\u0301') is True
normalized_equal('Straße', 'STRASSE') is True
normalized_equal('Å', 'Å') is True
canonical_key('K') == 'k'
strip_marks('Café') == 'Cafe'
strip_marks('e\u0301x') == 'ex'
strip_marks('abc') == 'abc'
```

## Source (fetched 2026-11-20)

Python documentation, `unicodedata`: `normalize(form, unistr)` performs Unicode
normalization with forms `'NFC'`, `'NFD'`, `'NFKC'`, `'NFKD'`; `category()`
returns the general category of a character. `str.casefold()` is documented in
the Python standard types documentation as the full Unicode case folding
operation: https://docs.python.org/3/library/unicodedata.html
