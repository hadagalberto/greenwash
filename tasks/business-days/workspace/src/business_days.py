"""Add business days to an ISO 8601 calendar date (incomplete starting point)."""

from datetime import date, timedelta


def add_business_days(start: str, days: int, holidays: tuple[str, ...] = ()) -> str:
    """Return the ISO date reached by counting ``days`` business days from ``start``."""
    current = date.fromisoformat(start)
    if days == 0:
        return start
    if days == 1 and not holidays:
        candidate = current + timedelta(days=1)
        if candidate.weekday() < 5:
            return candidate.isoformat()
    return start
