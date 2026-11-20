# EAN-13 and UPC-A check digits

Implement four functions in `src/ean.py`:

```python
def ean13_check_digit(payload12: str) -> str: ...
def is_valid_ean13(code: str) -> bool: ...
def upca_check_digit(payload11: str) -> str: ...
def is_valid_upca(code: str) -> bool: ...
```

## EAN-13

EAN-13 (European Article Number, now a GTIN-13) is described at
https://en.wikipedia.org/wiki/International_Article_Number and uses the GS1
check-digit scheme documented by GS1 at
https://www.gs1.org/how-calculate-check-digit-manually.

`payload12` is a string of exactly 12 ASCII digits `0`-`9`.

- Multiply the first twelve digits by weights that alternate `1, 3, 1, 3, ...`
  from left to right (the leftmost digit has weight 1) and sum the products.
- The check digit is `(10 - sum % 10) % 10`, returned as one character
  `"0"` ... `"9"`.

`is_valid_ean13(code)` returns `True` only when `code` is exactly 13 ASCII
digits (no separators, spaces or hyphens) and its last character equals
`ean13_check_digit(code[:12])`.

## UPC-A

UPC-A is the 12-digit predecessor of EAN-13; an EAN-13 with a leading zero is
the corresponding UPC-A.

`payload11` is a string of exactly 11 ASCII digits `0`-`9`.

- Multiply the eleven digits by weights that alternate `3, 1, 3, 1, ...` from
  left to right (the leftmost digit has weight 3) and sum the products.
- The check digit is `(10 - sum % 10) % 10`, returned as one character
  `"0"` ... `"9"`.

`is_valid_upca(code)` returns `True` only when `code` is exactly 12 ASCII
digits and its last character equals `upca_check_digit(code[:11])`.

Both validators must return `False` (never raise) for empty strings, wrong
lengths, non-digit characters or wrong check digits. The two weight patterns
must not be interchanged: EAN-13 starts with weight 1, UPC-A starts with
weight 3.

## Worked examples (from Wikipedia)

- EAN-13 `5901234123457` is valid. For payload `590123412345` the weighted
  sum is 83, so the check digit is `10 - 3 = 7`.
- EAN-13 `4006381333931` is valid: the weighted sum is 89, check digit 1.
- EAN-13 `5901234123456` is invalid (correct check digit is 7).
- UPC-A `036000291452` is valid. For payload `03600029145` the weighted sum
  is 58, so the check digit is 2.
- UPC-A `036000291453` is invalid (correct check digit is 2).

## Extra examples

- `ean13_check_digit("590123412345") == "7"`
- `ean13_check_digit("400638133393") == "1"`
- `upca_check_digit("03600029145") == "2"`
- `is_valid_ean13("59012341234567") is False` (14 digits)
- `is_valid_upca("03600029145") is False` (11 digits)
- `is_valid_ean13("590-1234123457") is False` (separators are not accepted)

## Sources (fetched 2026-11-20)

- https://en.wikipedia.org/wiki/International_Article_Number — "Calculation
  of checksum digit", "Position – weight" and "Calculation examples"; it gives
  the EAN-13 weights `131313131313`, the worked example `400638133393?` with
  checksum 89 and check digit 1, and notes that all GTIN check digits use
  alternating weights of 3 and 1 numbered from the right.
- https://www.gs1.org/how-calculate-check-digit-manually — GS1's official
  check-digit instructions: alternating weights `1, 3, 1, 3, ...` counted from
  the left for GTIN-13, and the worked example `629104150021` whose weighted
  sum is 57 and check digit is `3` (`6291041500213`).

Only `src/ean.py` needs changing; do not modify the test files or any other
module.
