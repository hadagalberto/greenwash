// Sliding-window rate limiter driven by an injected clock.
export class SlidingWindowLimiter {
  private readonly events = new Map<string, number[]>();

  private readonly maxEvents: number;
  private readonly windowMs: number;
  private readonly clock: () => number;

  constructor(maxEvents: number, windowMs: number, clock: () => number) {
    if (!Number.isInteger(maxEvents) || maxEvents < 1) {
      throw new RangeError('maxEvents must be a positive integer');
    }
    if (!Number.isFinite(windowMs) || windowMs <= 0) {
      throw new RangeError('windowMs must be positive and finite');
    }
    if (typeof clock !== 'function') {
      throw new RangeError('clock must be a function');
    }
    this.maxEvents = maxEvents;
    this.windowMs = windowMs;
    this.clock = clock;
  }

  private prune(key: string, now: number): number[] {
    const kept = (this.events.get(key) ?? []).filter((at) => at >= now - this.windowMs);
    this.events.set(key, kept);
    return kept;
  }

  allow(key: string = 'default'): boolean {
    const now = this.clock();
    const events = this.prune(key, now);
    if (events.length >= this.maxEvents) return false;
    events.push(now);
    return true;
  }

  count(key: string = 'default'): number {
    return this.prune(key, this.clock()).length;
  }
}
