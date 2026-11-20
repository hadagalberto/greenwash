// Straight-line principal amortisation with cent-rounded interest.
export interface ScheduleRow {
  month: number;
  paymentCents: number;
  principalCents: number;
  interestCents: number;
  balanceCents: number;
}

function roundHalfUp(numerator: number, denominator: number): number {
  return Math.floor((2 * numerator + denominator) / (2 * denominator));
}

export function buildSchedule(
  principalCents: number,
  annualRateBps: number,
  months: number,
): ScheduleRow[] {
  if (!Number.isInteger(principalCents) || principalCents < 0) throw new Error('bad principal');
  if (!Number.isInteger(annualRateBps) || annualRateBps < 0) throw new Error('bad rate');
  if (!Number.isInteger(months) || months < 1) throw new Error('bad months');
  const base = Math.floor(principalCents / months);
  const extra = principalCents % months;
  const rows: ScheduleRow[] = [];
  let balance = principalCents;
  for (let month = 1; month <= months; month += 1) {
    const principalPart = base + (months - month < extra ? 1 : 0);
    const interest = roundHalfUp(balance * annualRateBps, 120000);
    const payment = principalPart + interest;
    balance -= principalPart;
    rows.push({ month, paymentCents: payment, principalCents: principalPart,
                interestCents: interest, balanceCents: balance });
  }
  return rows;
}
