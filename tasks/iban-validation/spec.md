# IBAN validation (ISO 13616 / ISO-IEC 7064 MOD-97-10)

Implement two functions in `src/iban.py`:

- `is_valid(iban: str) -> bool`
- `mod97(iban: str) -> int`

## Normalization and structure

- Delete every space (`' '`) used for human grouping; then convert all letters to
  uppercase. Letters are case-insensitive: `gb82 west 1234 5698 7654 32` and
  `GB82WEST12345698765432` denote the same IBAN.
- The normalized string must consist only of ASCII letters `A`-`Z` and digits
  `0`-`9`.
- Its first two characters are the ISO 3166-1 alpha-2 country code (letters),
  the next two are decimal check digits, and the remainder is the BBAN
  (alphanumeric, possibly empty in the abstract, but length is fixed per
  country below).

## Supported countries and exact total lengths

Only these country codes are supported. The length is the total number of
characters **after** spaces are removed.

| Country code | Country | Total length |
| --- | --- | --- |
| `GB` | United Kingdom | 22 |
| `DE` | Germany | 22 |
| `IE` | Ireland | 22 |
| `FR` | France | 27 |
| `ES` | Spain | 24 |
| `NL` | Netherlands | 18 |
| `BE` | Belgium | 16 |

A different country code is invalid. A supported country with any other length
is invalid, even if its check digits happen to compute correctly.

## MOD-97-10 check (ISO/IEC 7064)

1. Move the first four characters of the normalized IBAN to the end.
2. Replace each letter by two decimal digits: `A`=10, `B`=11, ..., `Z`=35.
   Digits remain unchanged.
3. Interpret the expanded string as a decimal integer and take its remainder
   modulo 97.

`mod97(iban)` performs this normalization, rearrangement and expansion and
returns the remainder in `0..96`. It may be called on check-digit-invalid IBANs;
its input is assumed to have at least four alphanumeric characters after spaces
are removed.

`is_valid(iban)` returns `True` if and only if all normalization, character,
country, length and check-digit-format checks pass **and** `mod97(iban) == 1`.
Otherwise it returns `False` (it never raises for a malformed string).

## Official sources (fetched 2026-11-20)

- https://en.wikipedia.org/wiki/International_Bank_Account_Number — "Structure",
  "Validating the IBAN" (check that length matches the country, move the first
  four characters to the end, `A = 10, B = 11, ..., Z = 35`, remainder 1 means
  the check passes), the worked GB82 example, and the "IBAN formats by country"
  table. The table entries used above are: Belgium 16, Netherlands 18,
  United Kingdom 22, Germany 22, Ireland 22, Spain 24, France 27.
- https://www.swift.com/standards/iban — SWIFT is the ISO 13616 registration
  authority; the wikipedia article cites the SWIFT IBAN Registry, Release 99,
  December 2024, as the source of that country-length table.

## Worked example (from the wikipedia article)

```text
IBAN:       GB82 WEST 1234 5698 7654 32
normalized: GB82WEST12345698765432
rearranged: WEST12345698765432GB82
expanded:   3214282912345698765432161182
remainder:  3214282912345698765432161182 mod 97 = 1  -> valid
```

## Further examples

```text
IE64 IRCE 9205 0112 3456 78      -> valid (length 22)
DE89 3704 0044 0532 0130 00      -> valid (length 22)
FR76 3000 6000 0112 3456 7890 189 -> valid (length 27)
GB82WEST12345698765433           -> invalid (remainder 28, not 1)
GB82 WEST 1234 5698 7654 3       -> invalid (21 characters, not 22)
ZZ82 1234 5678                   -> invalid (unsupported country code)
gb82 west 1234 5698 7654 32      -> valid (letters are case-insensitive)
```

No file other than `src/iban.py` needs to change.
