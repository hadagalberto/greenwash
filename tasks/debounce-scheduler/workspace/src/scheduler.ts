// Skeleton interface (must be implemented by tests).
export interface Scheduler {
  now(): number;
  schedule(fn: () => void, delayMs: number): number;
  cancel(handle: number): void;
}
