// Skeleton: invokes immediately, ignores the scheduler.
import type { Scheduler } from './scheduler.ts';

export class Debouncer {
  constructor(_delayMs: number, _scheduler: Scheduler) {
    void _delayMs; void _scheduler;
  }

  get pendingCount(): number {
    return 0;
  }

  call(fn: () => void): void {
    fn();
  }

  flush(): void { }
  cancel(): void { }
}
