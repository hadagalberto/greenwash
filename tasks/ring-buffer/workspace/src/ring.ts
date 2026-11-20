// Skeleton: unbounded array, no wrap-around.
export class RingBuffer<T> {
  private readonly items: T[] = [];

  constructor(_capacity: number) {
    void _capacity;
  }

  push(value: T): T | undefined {
    this.items.push(value);
    return undefined;
  }

  shift(): T | undefined {
    return this.items.shift();
  }

  get size(): number {
    return this.items.length;
  }

  get isFull(): boolean {
    return false;
  }

  toArray(): T[] {
    return [...this.items];
  }

  clear(): void {
    this.items.length = 0;
  }
}
