# Banker's rounding of decimal strings

Implement `round_half_even(value: str, places: int) -> str` in
`src/rounding.py`.

## Input and output

- `value` is a **finite decimal string**: an optional leading `-`, then digits,
  optionally containing a single `.` with digits on at least one side. Examples:
  `"2"`, `"-0.5"`, `"2.675"`, `"123.456"`. There is no exponent part and no
  thousands separator.
- `places` is a non-negative integer number of fractional digits to keep.
- Return the correctly rounded decimal string with **exactly** `places`
  fractional digits. When `places == 0`, return an integer string with no `.`.
  Examples: `round_half_even("2", 0) == "2"`,
  `round_half_even("1", 2) == "1.00"`.

## Rounding rule (round half to even / banker's rounding)

Work on the exact decimal digits, never on a binary float. Let the digits after
the decimal point be split at position `places`:

- kept digits = digits up to and including place `places`;
- first discarded digit = the next digit;
- sticky = any later discarded digit is non-zero.

Then:

1. First discarded digit `> 5`, or `== 5` with `sticky` true: round **up**
   (add one unit to the last kept digit, carrying as needed).
2. First discarded digit `< 5`: round **down** (keep the kept digits).
3. First discarded digit `== 5` with `sticky` false: exact tie. Round **up only
   if the last kept digit is odd**; otherwise round down. This makes the last
   kept digit even. Missing digits are padded with zeros, so `"2"` to two
   places has kept digits `"200"` (last kept digit `0`, even).

Handle negatives by rounding the magnitude with the same rule and then
restoring the `-` sign for a non-zero result (ties go to the even digit of the
magnitude). The string `"0"` never becomes `"-0"`.

Using a binary float changes results: `2.675` is not exactly representable, so
`round(float("2.675"), 2)` gives `2.67`. The exact decimal string must give
`2.68` because the kept last digit `7` is odd.

## Official sources (fetched 2026-11-20)

- https://en.wikipedia.org/wiki/Rounding#Round_half_to_even — "if the
  fractional part of x is 0.5, then y is the even integer nearest to x";
  `23.5 -> 24`, `24.5 -> 24`, `-23.5 -> -24`, `-24.5 -> -24`. It also states
  that this is the default rounding mode of IEEE 754 binary floating point.
- https://docs.python.org/3/library/decimal.html#rounding-modes —
  `ROUND_HALF_EVEN`: "Round to nearest with ties going to nearest even integer."
  The same page shows the exact-decimal difference:
  `format(Decimal("2.675"), ".2f")` is `"2.68"`.

## Required examples

```text
round_half_even("2.5", 0)    == "2"
round_half_even("3.5", 0)    == "4"
round_half_even("1.25", 1)   == "1.2"
round_half_even("1.35", 1)   == "1.4"
round_half_even("0.5", 0)    == "0"
round_half_even("-2.5", 0)   == "-2"
round_half_even("-3.5", 0)   == "-4"
round_half_even("2.675", 2)  == "2.68"
round_half_even("1.005", 2)  == "1.00"
round_half_even("123.456", 1) == "123.5"
round_half_even("0", 3)      == "0.000"
round_half_even("1", 2)      == "1.00"
```

No file other than `src/rounding.py` needs to change.
