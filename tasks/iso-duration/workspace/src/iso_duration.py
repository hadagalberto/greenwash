# Skeleton: only handles whole years.
from __future__ import annotations

from collections.abc import Mapping

COMPONENTS = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")


def parse_duration(text: str) -> dict[str, int]:
    result = dict.fromkeys(COMPONENTS, 0)
    if text.startswith("P") and len(text) > 2:
        result["years"] = int(text[1:-1])
    return result


def format_duration(components: Mapping[str, int]) -> str:
    return "P0D"
