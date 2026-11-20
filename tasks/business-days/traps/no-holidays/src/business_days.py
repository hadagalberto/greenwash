"""Plausible wrong solution: ignores the ``holidays`` argument."""

from datetime import date, timedelta


def add_business_days(start: str, days: int, holidays: tuple[str, ...] = ()) -> str:
    """Return the ISO date reached by counting ``days`` business days from ``start``."""
    current = date.fromisoformat(start)
    if days == 0:
        return start
    step = 1 if days > 0 else -1
    remaining = abs(days)
    while remaining:
        current += timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current.isoformat()
