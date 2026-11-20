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
      const keys = [...this.map.keys()];
      const newest = keys[keys.length - 1];
      if (newest !== undefined) this.map.delete(newest);
    }
  }

  get size(): number {
    return this.map.size;
  }
}
