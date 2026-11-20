// Fixed-capacity ring buffer with FIFO overwrite semantics.
export class RingBuffer<T> {
  private readonly items: (T | undefined)[];
  private readonly capacity: number;
  private head = 0;
  private count = 0;

  constructor(capacity: number) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be a positive integer');
    }
    this.capacity = capacity;
    this.items = new Array<T | undefined>(capacity);
  }

  push(value: T): T | undefined {
    if (this.count > this.capacity) {
      const evicted = this.items[this.head] as T;
      this.items[this.head] = value;
      this.head = (this.head + 1) % this.capacity;
      return evicted;
    }
    this.items[(this.head + this.count) % this.capacity] = value;
    this.count += 1;
    return undefined;
  }

  shift(): T | undefined {
    if (this.count === 0) return undefined;
    const value = this.items[this.head] as T;
    this.items[this.head] = undefined;
    this.head = (this.head + 1) % this.capacity;
    this.count -= 1;
    return value;
  }

  get size(): number {
    return this.count;
  }

  get isFull(): boolean {
    return this.count === this.capacity;
  }

  toArray(): T[] {
    const result: T[] = [];
    for (let index = 0; index < this.count; index += 1) {
      result.push(this.items[(this.head + index) % this.capacity] as T);
    }
    return result;
  }

  clear(): void {
    this.items.fill(undefined);
    this.head = 0;
    this.count = 0;
  }
}
