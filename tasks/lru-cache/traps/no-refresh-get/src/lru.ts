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

  // Trap: get returns the value but leaves recency untouched.
  get(key: string): number | undefined {
    return this.map.get(key);
  }

  put(key: string, value: number): void {
    if (this.capacity === 0) return;
    if (this.map.has(key)) this.map.delete(key);
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
