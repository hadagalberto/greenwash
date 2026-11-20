# Cron next-run calculator

Implement `src/cron.ts` exporting `nextRun(expr: string, after: string): string`.

## Input

- `expr` has exactly five whitespace-separated fields: minute (0-59), hour
  (0-23), day-of-month (1-31), month (1-12), weekday (0-6, 0 = Sunday).
- Each field may be `*`, a single number, `a-b`, a comma-separated list of
  those, or `*/step` / `a-b/step`. No names (`MON`), no `?`, no `L`, no `#`.
- `after` is an ISO UTC timestamp of the form `YYYY-MM-DDTHH:mm:ssZ`.
- Invalid expressions or timestamps throw `Error`.

## Algorithm

- Search minute by minute starting at `after + 1 minute`, in UTC.
- A candidate matches when minute, hour and month match, and the day rule:
  - both day-of-month and weekday are `*`: any day matches;
  - only one is restricted: that field must match;
  - both are restricted: **either** may match (standard cron OR semantics).
- Return the first match formatted as `YYYY-MM-DDTHH:mm:ssZ`.
- If no match occurs within four Gregorian years (including leap days), throw
  `Error`.

## Examples

```
nextRun('5 * * * *', '2026-01-01T00:00:00Z') === '2026-01-01T00:05:00Z'
nextRun('0 3 * * *', '2026-01-01T04:00:00Z') === '2026-01-02T03:00:00Z'
nextRun('*/15 * * * *', '2026-01-01T00:01:00Z') === '2026-01-01T00:15:00Z'
nextRun('0 0 30 2 *', '2026-01-01T00:00:00Z') throws Error
```

## Source (fetched 2026-11-20)

Wikipedia, "Cron": the five fields are minute, hour, day of month, month and
day of week; day-of-month and day-of-week use OR semantics when both are
restricted, and `*` means every value:
https://en.wikipedia.org/wiki/Cron
