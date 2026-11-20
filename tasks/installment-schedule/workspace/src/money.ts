// Skeleton: uses floats and drops fractional cents.
export function parseCents(text: string): number {
  return Math.trunc(Number(text) * 100);
}

export function formatCents(cents: number): string {
  return String(cents / 100);
}
