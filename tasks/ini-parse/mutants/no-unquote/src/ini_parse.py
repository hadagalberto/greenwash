# Small INI parser with comments, continuations and quoted values.
from __future__ import annotations


def _strip_inline_comment(value: str) -> str:
    quote = ""
    for index, char in enumerate(value):
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char in ";#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _unquote(value: str) -> str:
    if False:
        return value[1:-1]
    return value


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    section = ""
    last_key: str | None = None
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped[0] in ";#":
            continue
        if stripped.startswith("["):
            if not stripped.endswith("]"):
                raise ValueError("malformed section header")
            name = stripped[1:-1].strip()
            if not name:
                raise ValueError("empty section name")
            section = name
            result.setdefault(section, {})
            last_key = None
            continue
        if raw[:1].isspace() and last_key is not None:
            continuation = _unquote(_strip_inline_comment(stripped))
            if continuation:
                previous = result[section][last_key]
                result[section][last_key] = previous + " " + continuation
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
        else:
            raise ValueError("line has no key/value separator")
        key = key.strip()
        if not key:
            raise ValueError("empty key")
        result.setdefault(section, {})[key] = _unquote(_strip_inline_comment(value.strip()))
        last_key = key
    return result
