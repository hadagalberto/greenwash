# Luhn check digit

Implement two functions in `src/luhn.py`:

```python
def luhn_check_digit(payload: str) -> str: ...
def is_valid(number: str) -> bool: ...
```

## Algorithm

The Luhn algorithm (also called the "modulus 10" or "mod 10" algorithm) is
specified in ISO/IEC 7812-1 Annex B and was published in US patent 2950048A.
It is described at https://en.wikipedia.org/wiki/Luhn_algorithm.

To compute the check digit for a `payload`:

1. The payload is a non-empty string of ASCII digits `0`-`9`.
2. Number the payload digits from the **right**, starting at 1 for the
   rightmost payload digit.
3. Double every digit in an **odd** position from the right (positions 1, 3,
   5, ...). Equivalently, for a 0-based index `i` from the left in a payload of
   length `n`, double the digit when `(n - 1 - i) % 2 == 0`. In particular the
   **rightmost payload digit is doubled**. For an even-length payload this
   doubles digits at odd 0-based indices from the left; for an odd-length
   payload it doubles digits at even 0-based indices from the left.
4. If a doubled value is greater than 9, subtract 9 from it.
5. Sum all resulting digits (doubled and not doubled).
6. The check digit is `(10 - sum % 10) % 10`, returned as a single character
   `"0"` ... `"9"`.

`is_valid(number)` returns `True` only when all of the following hold:

- `number` is a string of at least 2 characters;
- every character of `number` is an ASCII digit `0`-`9` (no spaces, hyphens or
  other separators are accepted anywhere);
- the final character of `number` equals `luhn_check_digit(number[:-1])`.

Otherwise `is_valid(number)` returns `False`. It must never raise for an
arbitrary string input, including the empty string.

## Worked example

For the payload `1789372997` (Wikipedia's example) the rightmost payload
digits in odd positions from the right are `7, 9, 7, 9, 7`. Doubling and
reducing gives `5, 9, 5, 9, 5` (sum 33). The undoubled digits are
`1, 8, 3, 2, 9` (sum 23). The total is 56, so the check digit is
`(10 - 56 % 10) % 10 = 4`, giving the full number `17893729974`.

## Examples

- `luhn_check_digit("1789372997") == "4"`
- `luhn_check_digit("7992739871") == "3"`
- `luhn_check_digit("411111111111111") == "1"` (odd-length payload)
- `is_valid("17893729974") is True`
- `is_valid("79927398713") is True`
- `is_valid("4111111111111111") is True`
- `is_valid("17893729975") is False` (wrong check digit)
- `is_valid("") is False` and `is_valid("7") is False` (too short)
- `is_valid("7992 7398 713") is False` (spaces are not accepted)
- `is_valid("12a") is False` (non-digit)

## Sources (fetched 2026-11-20)

- https://en.wikipedia.org/wiki/Luhn_algorithm — "Description", "Example for
  computing check digit", "Example for validating check digit" and the
  pseudocode section; it records the worked example `1789372997 -> 4` with sum
  56 and notes the algorithm is specified in ISO/IEC 7812-1 and US patent
  2950048A.
- https://www.iso.org/standard/70484.html — ISO/IEC 7812-1:2017,
  "Identification cards — Identification of issuers — Part 1: Numbering
  system", whose Annex B is the "Luhn formula for computing modulus-10
  double-add-double check digits".

Only `src/luhn.py` needs changing; do not modify the test files or any other
module.
