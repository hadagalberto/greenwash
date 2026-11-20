# Skeleton: raw string comparison, no normalization.
from __future__ import annotations


def canonical_key(text: str) -> str:
    return text


def normalized_equal(left: str, right: str) -> bool:
    return left == right


def strip_marks(text: str) -> str:
    return text
