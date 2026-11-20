# ISBN check digits

Implement two functions in `src/isbn.py`:

```python
def isbn10_check_digit(payload9: str) -> str: ...
def is_valid(isbn: str) -> bool: ...
```

The ISBN (International Standard Book Number) is defined by ISO 2108 and is
described at https://en.wikipedia.org/wiki/ISBN. Use the sections
"ISBN-10 check digit calculation" and "ISBN-13 check digit calculation".

## ISBN-10

`payload9` is a non-empty string of exactly 9 ASCII digits `0`-`9`.

- Multiply the first nine digits by the weights `10, 9, 8, ..., 2` from left to
  right and sum the products.
- The check value is `(11 - sum % 11) % 11`, an integer in `0` ... `10`.
- Return the check value as a single character: `str(value)` for `0` ... `9`,
  or the uppercase letter `"X"` when the value is `10`.

A complete ISBN-10 is 10 characters: the 9-digit payload followed by its check
character. The check character may be a digit or uppercase `X`.

## ISBN-13

A complete ISBN-13 is 13 ASCII digits. Its check digit is computed in the same
way as an EAN-13: multiply the first twelve digits by weights alternating
`1, 3, 1, 3, ...` from left to right (first digit weight 1), sum the products,
and use `(10 - sum % 10) % 10` as the final digit.

## What `is_valid` must do

- Hyphens `-` and spaces may appear **anywhere** in `isbn` and are ignored
  (removed) before validation. Any other non-digit character is invalid.
- After removing hyphens and spaces, the remaining string must have length 10
  or 13.
- For length 10: the first 9 characters must be ASCII digits and the last must
  be an ASCII digit or uppercase `X` (lowercase `x` is rejected). The check
  character must equal `isbn10_check_digit(first_nine)`.
- For length 13: all 13 characters must be ASCII digits and the last must
  equal the ISBN-13 check digit computed as described above.
- All other inputs are invalid. `is_valid` must return `False` (never raise)
  for empty strings, wrong lengths, wrong characters or wrong check digits.

## Worked examples (from Wikipedia)

- `isbn10_check_digit("030640615") == "2"`: the weighted sum is
  `0*10 + 3*9 + 0*8 + 6*7 + 4*6 + 0*5 + 6*4 + 1*3 + 5*2 = 130`, and
  `132 = 12*11`, so the check value is 2 and the ISBN is `0-306-40615-2`.
- `isbn10_check_digit("080442957") == "X"`: the weighted sum is 199 and the
  check value is 10, so the ISBN is `0-8044-2957-X`.
- `is_valid("978-3-16-148410-0") is True`: the ISBN-13 infobox example; the
  weighted sum of the first twelve digits is 100, giving check digit 0.
- `is_valid("9780306406157") is True`: the weighted sum is 93, giving 7.

## More examples

- `is_valid("0-306-40615-2") is True` and `is_valid("0 306 40615 2") is True`
- `is_valid("0-306-40615-7") is False` (wrong check character)
- `is_valid("0-8044-2957-x") is False` (lowercase `x` is not accepted)
- `is_valid("978-3-16-148410-1") is False` (wrong check digit)
- `is_valid("1234567890") is False` (correct check character would be `X`)
- `is_valid("030640615") is False` (wrong length)

## Sources (fetched 2026-11-20)

- https://en.wikipedia.org/wiki/ISBN — "Check digits", subsections
  "ISBN-10 check digits", "ISBN-10 check digit calculation" (worked example
  `0-306-40615-2`, sum 130, check 2, and the rule that value 10 is written
  `X`) and "ISBN-13 check digit calculation" (alternating 1 and 3 weights,
  infobox example `978-3-16-148410-0`); the article identifies ISO 2108 as
  the governing standard.

Only `src/isbn.py` needs changing; do not modify the test files or any other
module.
