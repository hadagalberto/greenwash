# Rational arithmetic on `(numerator, denominator)` pairs

Implement these functions in `src/rational.py`. A rational is a plain
`tuple[int, int]` `(numerator, denominator)` with `denominator != 0`.
Inputs may be unreduced and may have a negative denominator; for example
`(2, -4)` means `-1/2`.

```python
def add(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]
def sub(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]
def mul(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]
def div(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]
def compare(a: tuple[int, int], b: tuple[int, int]) -> int
```

## Canonical result form

Every result of `add`, `sub`, `mul` and `div` must be:

- in lowest terms (divide numerator and denominator by their greatest common
  divisor);
- with a **positive** denominator (move the sign to the numerator when needed);
- exactly `(0, 1)` for zero, regardless of the input representation.

`div` raises `ZeroDivisionError` when the numerator of `b` is zero (dividing by
zero), matching Python's `fractions.Fraction` constructor, which raises
`ZeroDivisionError` for a zero denominator.

`compare` returns `-1` if `a < b`, `0` if `a == b`, and `1` if `a > b`. It must
normalize signs before comparing: `(1, -2)` and `(-2, 4)` are equal (`-1/2`).
Equality of fractions is defined by the cross product `a.numerator *
b.denominator == b.numerator * a.denominator` once denominators are positive.

## Algebraic definitions

With `a = (n1, d1)` and `b = (n2, d2)` (before reduction):

```text
add(a, b) = (n1*d2 + n2*d1, d1*d2)
sub(a, b) = (n1*d2 - n2*d1, d1*d2)
mul(a, b) = (n1*n2,         d1*d2)
div(a, b) = (n1*d2,         d1*n2)      requires n2 != 0
```

## Official sources (fetched 2026-11-20)

- https://docs.python.org/3/library/fractions.html — `Fraction(16, -10)` is
  `Fraction(-8, 5)`; the `denominator` property is "guaranteed to be positive";
  a zero denominator raises `ZeroDivisionError`; `math.gcd` is used to
  normalize. `Fraction(0, 5)` prints as `Fraction(0, 1)`.
- https://en.wikipedia.org/wiki/Fraction_(mathematics) — "Arithmetic with
  fractions": operations on ordered pairs `(a,b)+(c,d)=(ad+bc,bd)` etc.,
  "Comparing fractions" by cross multiplication, and "Simplifying (reducing)
  fractions": division by the greatest common divisor gives lowest terms.
  The article also states `-1/2 = 1/-2` (sign normalization).

## Required examples

```text
add((1, 2), (-1, 3))  == (1, 6)
add((1, -2), (1, 3))  == (-1, 6)
add((2, 4), (1, -6))  == (1, 3)      # 1/2 - 1/6 = 1/3
sub((1, 2), (1, 3))   == (1, 6)
mul((-2, 3), (3, -4)) == (1, 2)
mul((2, -4), (-3, 6)) == (1, 4)
div((-2, 3), (4, -5)) == (5, 6)
div((1, 2), (-2, 3))  == (-3, 4)
compare((-1, 2), (1, -3)) == -1
compare((1, -2), (-2, 4)) == 0
compare((3, 4), (2, 3)) == 1
div((1, 2), (0, 5)) raises ZeroDivisionError
```

No file other than `src/rational.py` needs to change.
