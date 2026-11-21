// Exact decimal-string to cents conversion.
export function parseCents(text: string): number {
  if (typeof text !== 'string') throw new Error('bad amount');
  const trimmed = text.trim();
  if (!/^-?\d+(\.\d{1,2})?$/.test(trimmed)) throw new Error('bad amount');
  const negative = trimmed.startsWith('-');
  const body = negative ? trimmed.slice(1) : trimmed;
  const [whole, fraction = ''] = body.split('.');
  const cents = Number(whole) * 100 + Number((fraction + '00').slice(0, 2));
  if (!Number.isSafeInteger(cents)) throw new Error('amount too large');
  return negative ? -cents : cents;
}

export function formatCents(cents: number): string {
  if (!Number.isInteger(cents)) throw new Error('bad cents');
  const sign = cents < 0 ? '-' : '';
  const magnitude = Math.abs(cents);
  return `${sign}${Math.floor(magnitude / 100)}.${String(magnitude % 100)}`;
}
