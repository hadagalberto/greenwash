"""Trap: computes correctly but restores the first operand's denominator sign."""

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


def _with_first_sign(result: Rational, a: Rational) -> Rational:
    if a[1] < 0:
        return (-result[0], -result[1])
    return result


def add(a: Rational, b: Rational) -> Rational:
    return _with_first_sign(_normalize(a[0] * b[1] + b[0] * a[1], a[1] * b[1]), a)


def sub(a: Rational, b: Rational) -> Rational:
    return _with_first_sign(_normalize(a[0] * b[1] - b[0] * a[1], a[1] * b[1]), a)


def mul(a: Rational, b: Rational) -> Rational:
    return _with_first_sign(_normalize(a[0] * b[0], a[1] * b[1]), a)


def div(a: Rational, b: Rational) -> Rational:
    if b[0] == 0:
        raise ZeroDivisionError("division by zero rational")
    return _with_first_sign(_normalize(a[0] * b[1], a[1] * b[0]), a)


def compare(a: Rational, b: Rational) -> int:
    n1, d1 = _normalize(*a)
    n2, d2 = _normalize(*b)
    left, right = n1 * d2, n2 * d1
    return (left > right) - (left < right)
