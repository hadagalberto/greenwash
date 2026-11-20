// HTTP Retry-After parsing into an absolute timestamp (milliseconds).
export function parseRetryAfter(header: string, nowMs: number): number {
  if (typeof header !== 'string') throw new Error('bad header');
  if (typeof nowMs !== 'number' || !Number.isFinite(nowMs)) throw new Error('bad nowMs');
  const text = header;
  if (/^\d+$/.test(text)) return nowMs + Number(text) * 1000;
  const parsed = Date.parse(text);
  if (!Number.isFinite(parsed)) throw new Error('bad date');
  if (new Date(parsed).toUTCString() !== text) throw new Error('non-canonical date');
  return parsed;
}
