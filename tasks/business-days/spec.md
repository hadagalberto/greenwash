# Add business days to an ISO 8601 date

Implement `src/business_days.py` exporting:

```python
def add_business_days(start: str, days: int, holidays: tuple[str, ...] = ()) -> str
```

Dates are ISO 8601 extended-format calendar dates, `YYYY-MM-DD` (year, then
month, then day; most significant component first, hyphen separators). See
ISO 8601, "Calendar dates" (fetched 2026-11-20):
https://en.wikipedia.org/wiki/ISO_8601. Weekday facts used below (which dates
are Mondays, Fridays, weekends, etc.) were checked against
https://www.timeanddate.com/calendar/ (fetched 2026-11-20) and with Python's
`datetime.date.weekday()` (Monday = 0 through Sunday = 6).

A **business day** is a date that is Monday through Friday and is not listed in
`holidays`. Holiday strings are exact dates only: no observance shifting (a
holiday falling on a Saturday is not moved to the following Monday).

Semantics:

- `days > 0`: count business days strictly **after** `start`; `start` itself is
  never counted.
- `days < 0`: count business days strictly **before** `start`; `start` itself is
  never counted.
- `days == 0`: return `start` unchanged, even if `start` is a weekend or a
  holiday.

Return the resulting date as an ISO `YYYY-MM-DD` string.

## Examples (weekdays verified while authoring)

- `2024-01-01` is a Monday.
  - `add_business_days("2024-01-01", 1, ()) == "2024-01-02"` (Tuesday).
  - `add_business_days("2024-01-01", -1, ()) == "2023-12-29"` (the preceding
    Friday; the weekend in between is skipped).
  - `add_business_days("2024-01-01", 0, ()) == "2024-01-01"`.
- `2024-01-05` is a Friday: `add_business_days("2024-01-05", 1, ()) ==
  "2024-01-08"` (Monday; Saturday and Sunday are skipped).
- With a holiday: `add_business_days("2024-01-05", 1, ("2024-01-08",)) ==
  "2024-01-09"` (Monday is excluded, so Tuesday is the first business day).
- Multiple weekdays plus a holiday:
  `add_business_days("2024-01-01", 5, ("2024-01-02",)) == "2024-01-09"`.
  The five counted days are Wed 01-03, Thu 01-04, Fri 01-05, Mon 01-08 and
  Tue 01-09; 01-02 is a holiday and the 01-06/01-07 weekend is skipped.
- Backwards with a holiday: `add_business_days("2024-01-08", -1,
  ("2024-01-05",)) == "2024-01-04"`.
