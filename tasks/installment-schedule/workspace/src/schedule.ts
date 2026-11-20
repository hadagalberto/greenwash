// Skeleton: no interest, one row.
export interface ScheduleRow {
  month: number;
  paymentCents: number;
  principalCents: number;
  interestCents: number;
  balanceCents: number;
}

export function buildSchedule(
  principalCents: number,
  _annualRateBps: number,
  _months: number,
): ScheduleRow[] {
  void _annualRateBps; void _months;
  return [{ month: 1, paymentCents: principalCents, principalCents,
            interestCents: 0, balanceCents: 0 }];
}
