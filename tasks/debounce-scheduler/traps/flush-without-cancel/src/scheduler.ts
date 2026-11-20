// Minimal deterministic timer interface used by the debouncer.
export interface Scheduler {
  now(): number;
  schedule(fn: () => void, delayMs: number): number;
  cancel(handle: number): void;
}
