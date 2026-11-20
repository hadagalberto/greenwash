"""Rational arithmetic - incomplete starting point; implement the rules in spec.md."""

from __future__ import annotations

Rational = tuple[int, int]


def add(a: Rational, b: Rational) -> Rational:
    """Return the reduced sum of two rationals."""
    return (0, 1)


def sub(a: Rational, b: Rational) -> Rational:
    """Return the reduced difference of two rationals."""
    return (0, 1)


def mul(a: Rational, b: Rational) -> Rational:
    """Return the reduced product of two rationals."""
    return (0, 1)


def div(a: Rational, b: Rational) -> Rational:
    """Return the reduced quotient of two rationals."""
    return (0, 1)


def compare(a: Rational, b: Rational) -> int:
    """Return -1, 0 or 1 according to the ordering of two rationals."""
    return 0
