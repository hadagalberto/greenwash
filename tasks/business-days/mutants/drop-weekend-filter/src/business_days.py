"""Add business days to an ISO 8601 calendar date."""

from datetime import date, timedelta


def add_business_days(start: str, days: int, holidays: tuple[str, ...] = ()) -> str:
    """Return the ISO date reached by counting ``days`` business days from ``start``."""
    current = date.fromisoformat(start)
    excluded = set(holidays)
    if days == 0:
        return start
    step = 1 if days > 0 else -1
    remaining = abs(days)
    while remaining:
        current += timedelta(days=step)
        if current.isoformat() not in excluded:
            remaining -= 1
    return current.isoformat()
