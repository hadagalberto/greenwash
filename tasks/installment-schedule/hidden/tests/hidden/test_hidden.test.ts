// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: Throw `Error` if the result is not a safe integer.
//     -> invalid schedule parameters throw, all cents are allocated exactly once, exact money
//       parsing
// R2: - `formatCents(cents: number): string`: integer input only; return a ...
//     -> all cents are allocated exactly once, money parsing trims and formatting pads to two
//       digits, remainder cents go to the earliest installments
//
// Hand-computed amortisation and cent vectors.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseCents, formatCents } from '../../src/money.ts';
import { buildSchedule } from '../../src/schedule.ts';

test('remainder cents go to the earliest installments', () => {
  const rows = buildSchedule(1000, 0, 3);
  assert.deepEqual(rows.map((row) => row.principalCents), [334, 333, 333]);
  assert.deepEqual(rows.map((row) => row.paymentCents), [334, 333, 333]);
  assert.deepEqual(rows.map((row) => row.balanceCents), [666, 333, 0]);
});

test('interest is computed on the declining balance', () => {
  const rows = buildSchedule(100000, 500, 2);
  assert.deepEqual(rows.map((row) => row.interestCents), [417, 208]);
  assert.deepEqual(rows.map((row) => row.paymentCents), [50417, 50208]);
  assert.deepEqual(rows.map((row) => row.balanceCents), [50000, 0]);
});

test('half-up tie on interest', () => {
  const rows = buildSchedule(600, 500, 1);
  assert.equal(rows[0].interestCents, 3);
  assert.equal(rows[0].paymentCents, 603);
});

test('all cents are allocated exactly once', () => {
  for (const [principal, months] of [[1001, 7], [999, 4], [1, 3]] as [number, number][]) {
    const rows = buildSchedule(principal, 0, months);
    assert.equal(rows.reduce((sum, row) => sum + row.principalCents, 0), principal);
  }
});

test('exact money parsing', () => {
  assert.equal(parseCents('0.10'), 10);
  assert.equal(parseCents('-0.50'), -50);
  assert.equal(parseCents('7'), 700);
  assert.equal(formatCents(5), '0.05');
  assert.equal(formatCents(-5), '-0.05');
  assert.throws(() => parseCents('1e3'), Error);
});

test('invalid schedule parameters throw', () => {
  assert.throws(() => buildSchedule(-1, 0, 1), Error);
  assert.throws(() => buildSchedule(1, 0, 0), Error);
  assert.throws(() => buildSchedule(1, -1, 1), Error);
});

test('money parsing trims and formatting pads to two digits', () => {
  // spec.md: trim before the decimal regex; -0.50 -> -50; formatCents(1234).
  assert.equal(parseCents('  -0.50  '), -50);
  assert.equal(parseCents('12.3'), 1230);
  assert.equal(formatCents(1234), '12.34');
  assert.throws(() => formatCents(1.5), Error);
  assert.throws(() => parseCents('.5'), Error);
});

test('zero-rate schedule splits principal evenly with no interest', () => {
  // spec.md example: buildSchedule(900, 0, 3).
  const rows = buildSchedule(900, 0, 3);
  assert.deepEqual(rows.map((row) => row.month), [1, 2, 3]);
  assert.deepEqual(rows.map((row) => row.principalCents), [300, 300, 300]);
  assert.deepEqual(rows.map((row) => row.interestCents), [0, 0, 0]);
  assert.deepEqual(rows.map((row) => row.balanceCents), [600, 300, 0]);
});
