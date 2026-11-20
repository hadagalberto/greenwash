"""Plausible wrong solution: always steps forward, even for negative counts."""

from datetime import date, timedelta


def add_business_days(start: str, days: int, holidays: tuple[str, ...] = ()) -> str:
    """Return the ISO date reached by counting ``days`` business days from ``start``."""
    current = date.fromisoformat(start)
    excluded = set(holidays)
    if days == 0:
        return start
    remaining = abs(days)
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5 and current.isoformat() not in excluded:
            remaining -= 1
    return current.isoformat()
