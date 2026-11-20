// Least-recently-used cache (incomplete starting point).

export class LruCache {
  private readonly map = new Map<string, number>();

  constructor(capacity: number) {
    // Naive placeholder: capacity is ignored.
    void capacity;
  }

  get(key: string): number | undefined {
    return this.map.get(key);
  }

  put(key: string, value: number): void {
    this.map.set(key, value);
  }

  get size(): number {
    return this.map.size;
  }
}
