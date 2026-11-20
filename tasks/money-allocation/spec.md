# Money allocation by largest remainder

Implement `allocate(amount_cents: int, weights: Sequence[int]) -> list[int]`
in `src/allocate.py`.

## Contract

- `amount_cents` is a non-negative `int` (not `bool`).
- `weights` is a non-empty sequence of non-negative `int` values (not `bool`).
- `sum(weights)` must be positive.
- Any violation of those constraints raises `ValueError`.

## Algorithm (Hamilton / largest remainder)

Let `total = sum(weights)` and `products[i] = amount_cents * weights[i]`.

1. Give every index its integer share `products[i] // total`.
2. The leftover is `amount_cents - sum(floor shares)`; it is between `0` and
   `len(weights) - 1`.
3. Compute `remainders[i] = products[i] % total`. Sort indices by
   `(-remainder, index)` — **largest remainder first, ties to the lowest index** —
   and add one cent to each of the first `leftover` indices in that order.

The result is a list with exactly `len(weights)` non-negative integers whose sum
is exactly `amount_cents`. Zero weights always receive zero cents.

## Examples

```
allocate(100, [1, 2, 3, 4]) == [10, 20, 30, 40]
allocate(12, [1, 1, 1])     == [4, 4, 4]
allocate(1, [1, 1, 1])      == [1, 0, 0]      # tie -> lowest index
allocate(5, [1, 1, 1])      == [2, 2, 1]      # three equal remainders
allocate(10, [1, 2, 3])     == [2, 3, 5]      # remainders 4, 2, 0 over quota 6
allocate(10, [0, 1, 0])     == [0, 10, 0]
allocate(0, [5, 5])         == [0, 0]
allocate(-1, [1])           raises ValueError
allocate(1, [0, 0])         raises ValueError
```

## Source (fetched 2026-11-20)

Wikipedia, "Largest remainder method": each party first receives the integer
part of its entitlement, then leftover seats go to the parties with the largest
fractional remainders (Hare/Hamilton quota):
https://en.wikipedia.org/wiki/Largest_remainder_method
The lowest-index tie break in this task is a spec-defined determinism rule, not
part of the electoral method.
