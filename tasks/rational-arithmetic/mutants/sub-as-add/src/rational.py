"""Mutant: subtraction accidentally calls the addition formula."""

from __future__ import annotations

from math import gcd

Rational = tuple[int, int]


def _normalize(numerator: int, denominator: int) -> Rational:
    if denominator == 0:
        raise ZeroDivisionError("zero denominator")
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    if numerator == 0:
        return (0, 1)
    divisor = gcd(numerator, denominator)
    return (numerator // divisor, denominator // divisor)


def add(a: Rational, b: Rational) -> Rational:
    return _normalize(a[0] * b[1] + b[0] * a[1], a[1] * b[1])


def sub(a: Rational, b: Rational) -> Rational:
    return _normalize(a[0] * b[1] + b[0] * a[1], a[1] * b[1])


def mul(a: Rational, b: Rational) -> Rational:
    return _normalize(a[0] * b[0], a[1] * b[1])


def div(a: Rational, b: Rational) -> Rational:
    if b[0] == 0:
        raise ZeroDivisionError("division by zero rational")
    return _normalize(a[0] * b[1], a[1] * b[0])


def compare(a: Rational, b: Rational) -> int:
    n1, d1 = _normalize(*a)
    n2, d2 = _normalize(*b)
    left, right = n1 * d2, n2 * d1
    return (left > right) - (left < right)
