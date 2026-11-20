# ISO 8601 duration parser and canonical formatter (integer components only).
from __future__ import annotations

from collections.abc import Mapping

COMPONENTS = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")
_DESIGNATORS = (
    ("years", "Y"),
    ("months", "M"),
    ("weeks", "W"),
    ("days", "D"),
    ("hours", "H"),
    ("minutes", "M"),
    ("seconds", "S"),
)


def parse_duration(text: str) -> dict[str, int]:
    if not isinstance(text, str) or not text.startswith("P") or len(text) < 2:
        raise ValueError("invalid duration")
    body = text[1:]
    if body.count("T") > 1:
        raise ValueError("invalid T")
    if "T" in body:
        date_part, time_part = body.split("T")
        if not time_part:
            raise ValueError("empty time part")
    else:
        date_part, time_part = body, ""
    result = dict.fromkeys(COMPONENTS, 0)
    for segment, in_time in ((date_part, False), (time_part, True)):
        allowed = _DESIGNATORS[4:] if in_time else _DESIGNATORS[:4]
        last_position = -1
        index = 0
        while index < len(segment):
            start = index
            while index < len(segment) and segment[index].isdigit():
                index += 1
            if start == index or index >= len(segment):
                raise ValueError("invalid component")
            number = int(segment[start:index])
            unit = segment[index]
            index += 1
            matches = [(pos, name) for pos, (name, symbol) in enumerate(allowed) if symbol == unit]
            if len(matches) != 1:
                raise ValueError("unknown unit")
            position, name = matches[0]
            if position <= last_position:
                raise ValueError("duplicate or out-of-order unit")
            last_position = position
            result["days" if name == "weeks" else name] = number
    return result


def format_duration(components: Mapping[str, int]) -> str:
    for name in COMPONENTS:
        value = components.get(name, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("invalid component")
    date = "".join(
        f"{components.get(name, 0)}{symbol}"
        for name, symbol in _DESIGNATORS[:4]
        if components.get(name, 0)
    )
    time = "".join(
        f"{components.get(name, 0)}{symbol}"
        for name, symbol in _DESIGNATORS[4:]
        if components.get(name, 0)
    )
    if not date and not time:
        return "P0D"
    return "P" + date + ("T" + time if time else "")
