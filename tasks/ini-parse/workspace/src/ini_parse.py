# Skeleton: only sections and '=' pairs, no comments or continuations.
from __future__ import annotations


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    section = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            result[section] = {}
        elif "=" in line:
            key, value = line.split("=", 1)
            result.setdefault(section, {})[key.strip()] = value.strip()
    return result
