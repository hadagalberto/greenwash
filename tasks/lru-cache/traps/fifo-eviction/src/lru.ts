// Least-recently-used cache. Map iteration order is least -> most recent.

export class LruCache {
  private readonly map = new Map<string, number>();
  private readonly capacity: number;

  constructor(capacity: number) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError("capacity must be a non-negative integer");
    }
    this.capacity = capacity;
  }

  // Trap: FIFO eviction — a hit does not refresh recency.
  get(key: string): number | undefined {
    return this.map.get(key);
  }

  put(key: string, value: number): void {
    if (this.capacity === 0) return;
    // Trap: updating a key keeps its original insertion position.
    this.map.set(key, value);
    if (this.map.size > this.capacity) {
      const oldest = this.map.keys().next().value;
      if (oldest !== undefined) this.map.delete(oldest);
    }
  }

  get size(): number {
    return this.map.size;
  }
}
