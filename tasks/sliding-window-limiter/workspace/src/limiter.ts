// Skeleton: never limits, clock ignored.
export class SlidingWindowLimiter {
  constructor(_maxEvents: number, _windowMs: number, _clock: () => number) {
    void _maxEvents; void _windowMs; void _clock;
  }

  allow(_key: string = 'default'): boolean {
    return true;
  }

  count(_key: string = 'default'): number {
    return 0;
  }
}
