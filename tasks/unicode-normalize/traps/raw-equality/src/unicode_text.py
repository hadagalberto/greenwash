# Unicode canonicalization based on Python's unicodedata module.
from __future__ import annotations

import unicodedata


def canonical_key(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return text


def normalized_equal(left: str, right: str) -> bool:
    return canonical_key(left) == canonical_key(right)


def strip_marks(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    decomposed = unicodedata.normalize("NFD", text)
    bare = "".join(char for char in decomposed if not unicodedata.category(char).startswith("M"))
    return unicodedata.normalize("NFC", bare)
