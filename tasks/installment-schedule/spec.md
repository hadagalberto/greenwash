# Installment schedule without losing cents

Implement `src/money.ts` and `src/schedule.ts`.

## `src/money.ts`

- `parseCents(text: string): number`: accept `^-?\d+(\.\d{1,2})?$` after
  trimming, else throw `Error`. Convert exactly to integer cents (no binary
  float rounding). `-0.50` becomes `-50`. Throw `Error` if the result is not a
  safe integer.
- `formatCents(cents: number): string`: integer input only; return a signed
  decimal string with exactly two fractional digits (`1234 -> "12.34"`,
  `-5 -> "-0.05"`). Non-integer throws `Error`.

## `src/schedule.ts`

`buildSchedule(principalCents, annualRateBps, months)` returns one row per
month with fields `month, paymentCents, principalCents, interestCents,
balanceCents`.

- Validate: `principalCents` non-negative integer, `annualRateBps`
  non-negative integer (basis points; 500 = 5%), `months` positive integer;
  otherwise throw `Error`.
- `base = floor(principalCents / months)`, `extra = principalCents % months`.
  Installments `1..extra` receive one extra cent of principal (so all cents
  are allocated to the **earliest** installments).
- Monthly interest = `roundHalfUp(balance * annualRateBps / 120000)` where
  `balance` is the remaining principal **before** the installment and
  `roundHalfUp(n, d) = floor((2n + d) / (2d))` (half rounds up).
- `paymentCents = principalCents(slice) + interest`; then subtract the
  principal slice from `balance`. Rows are in month order.

## Examples

```
buildSchedule(900, 0, 3)  // principal slices 300, 300, 300; interest 0
buildSchedule(1000, 0, 3) // principal slices 334, 333, 333
buildSchedule(100000, 500, 2)
  // month 1 interest 417, principal 50000, payment 50417, balance 50000
  // month 2 interest 208, principal 50000, payment 50208, balance 0
buildSchedule(600, 500, 1) // interest 2.5 cents -> 3; payment 603
```

## Source (fetched 2026-11-20)

Wikipedia, "Amortization calculator": an amortisation schedule shows each
payment split into interest and principal with a declining balance:
https://en.wikipedia.org/wiki/Amortization_calculator
The cent-allocation and rounding rules above are spec-defined.
