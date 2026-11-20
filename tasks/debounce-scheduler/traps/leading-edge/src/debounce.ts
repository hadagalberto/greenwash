// Trailing-edge debounce with a fully injected scheduler.
import type { Scheduler } from './scheduler.ts';

export class Debouncer {
  private handle: number | null = null;
  private pending: (() => void) | null = null;
  private readonly delayMs: number;
  private readonly scheduler: Scheduler;

  constructor(delayMs: number, scheduler: Scheduler) {
    if (!Number.isFinite(delayMs) || delayMs < 0) {
      throw new RangeError('delayMs must be finite and non-negative');
    }
    this.delayMs = delayMs;
    this.scheduler = scheduler;
  }

  get pendingCount(): number {
    return this.pending === null ? 0 : 1;
  }

  call(fn: () => void): void {
    if (typeof fn !== 'function') throw new TypeError('fn must be a function');
    if (this.handle !== null) this.scheduler.cancel(this.handle);
    fn();
    this.pending = null;
    this.handle = this.scheduler.schedule(() => {
      const current = this.pending;
      this.pending = null;
      this.handle = null;
      if (current !== null) current();
    }, this.delayMs);
  }

  flush(): void {
    if (this.handle !== null) this.scheduler.cancel(this.handle);
    const current = this.pending;
    this.pending = null;
    this.handle = null;
    if (current !== null) current();
  }

  cancel(): void {
    if (this.handle !== null) this.scheduler.cancel(this.handle);
    this.pending = null;
    this.handle = null;
  }
}
