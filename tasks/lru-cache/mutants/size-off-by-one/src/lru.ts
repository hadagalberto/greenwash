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

  get(key: string): number | undefined {
    if (!this.map.has(key)) return undefined;
    const value = this.map.get(key) as number;
    this.map.delete(key);
    this.map.set(key, value);
    return value;
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
    // Mutant: reports one extra entry.
    return this.map.size + 1;
  }
}
