// Minimal five-field UTC cron with minute resolution.
function parseField(text: string, min: number, max: number): Set<number> {
  const result = new Set<number>();
  for (const piece of text.split(',')) {
    if (piece === '') throw new Error('empty cron piece');
    const [range, stepText] = piece.split('/');
    if (stepText !== undefined && !/^\d+$/.test(stepText)) throw new Error('bad step');
    const step = stepText === undefined ? 1 : Number(stepText);
    if (step < 1) throw new Error('bad step');
    let low: number;
    let high: number;
    if (range === '*') {
      low = min; high = max;
    } else if (/^\d+-\d+$/.test(range)) {
      const parts = range.split('-').map(Number);
      low = parts[0]; high = parts[1];
    } else if (/^\d+$/.test(range)) {
      low = Number(range); high = Number(range);
    } else {
      throw new Error('bad range');
    }
    if (low < min || high > max || low > high) throw new Error('range out of bounds');
    for (let value = low; value <= high; value += step) result.add(value);
  }
  return result;
}

export function nextRun(expr: string, after: string): string {
  const fields = expr.trim().split(/\s+/);
  if (fields.length !== 5) throw new Error('expected five fields');
  const minutes = parseField(fields[0], 0, 59);
  const hours = parseField(fields[1], 0, 23);
  const days = parseField(fields[2], 1, 31);
  const months = parseField(fields[3], 1, 12);
  const weekdays = parseField(fields[4], 0, 6);
  const afterMs = Date.parse(after);
  if (!Number.isFinite(afterMs)) throw new Error('bad timestamp');
  let time = Math.floor(afterMs / 60000) * 60000;
  const limit = time + 4 * 366 * 24 * 60 * 60000;
  const domRestricted = fields[2] !== '*';
  const dowRestricted = fields[4] !== '*';
  while (time <= limit) {
    const date = new Date(time);
    const month = date.getUTCMonth() + 1;
    const day = date.getUTCDate();
    const weekday = date.getUTCDay();
    let dayMatches = true;
    if (domRestricted && dowRestricted) dayMatches = days.has(day) || weekdays.has(weekday);
    else if (domRestricted) dayMatches = days.has(day);
    else if (dowRestricted) dayMatches = weekdays.has(weekday);
    if (minutes.has(date.getUTCMinutes()) && hours.has(date.getUTCHours()) &&
        months.has(month) && dayMatches) {
      return new Date(time).toISOString().slice(0, 19) + 'Z';
    }
    time += 60000;
  }
  throw new Error('no matching time');
}
