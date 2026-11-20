# Retry-After parser

Implement `parseRetryAfter(header: string, nowMs: number): number` in
`src/retry_after.ts`. It returns an **absolute** time in milliseconds since
the epoch. All time comes from the `nowMs` argument, never the real clock.

## Rules

- Non-string header or non-finite `nowMs` throws `Error`.
- Trim surrounding whitespace from `header`.
- If the trimmed header is `/^\d+$/` (non-negative integer seconds), return
  `nowMs + seconds * 1000`.
- Otherwise the header must be an IMF-fixdate such as
  `Sun, 06 Nov 1994 08:49:37 GMT`. Parse it as UTC; the parse must be finite
  and `new Date(parsed).toUTCString()` must equal the trimmed header exactly
  (this rejects obsolete RFC 850 / asctime forms and impossible dates).
  Return `parsed`.
- Anything else throws `Error`.

## Examples

```
parseRetryAfter('2', 0) === 2000
parseRetryAfter(' 10 ', 5000) === 15000
parseRetryAfter('Sun, 06 Nov 1994 08:49:37 GMT', 0) === 784111777000
parseRetryAfter('-2', 0) throws Error
parseRetryAfter('Sunday, 06-Nov-94 08:49:37 GMT', 0) throws Error
```

## Source (fetched 2026-11-20)

RFC 9110, section 10.2.3 "Retry-After": the value is either a non-negative
integer number of seconds or an HTTP-date (IMF-fixdate preferred):
https://www.rfc-editor.org/rfc/rfc9110.txt
Returning an absolute timestamp using the injected `nowMs` is spec-defined.
