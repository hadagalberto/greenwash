# Skeleton: calls the operation once, no retry.
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], **kwargs: object) -> T:
    return operation()
