# Ring buffer

Implement `src/ring.ts` exporting `class RingBuffer<T>`:

```ts
constructor(capacity: number)
push(value: T): T | undefined
shift(): T | undefined
get size(): number
get isFull(): boolean
toArray(): T[]
clear(): void
```

## Contract

- `capacity` must be a positive integer, else `RangeError`.
- `push` appends. When the buffer is full, it overwrites the **oldest** item,
  returns that evicted item, and advances the read position. Otherwise it
  returns `undefined`.
- `shift` removes and returns the oldest item, or `undefined` when empty.
- `toArray` returns items oldest-to-newest (logical order, not storage order).
- `size` is the number of stored items; `isFull` is `size === capacity`.
- `clear` empties the buffer and resets the internal positions.

## Examples

```
const b = new RingBuffer<string>(3);
b.push('a'); b.push('b'); b.push('c');
b.isFull === true; b.toArray() === ['a','b','c']
b.push('d') === 'a'; b.toArray() === ['b','c','d']
b.shift() === 'b'; b.toArray() === ['c','d']
```

## Source (fetched 2026-11-20)

Wikipedia, "Circular buffer": a fixed-size buffer that overwrites the oldest
element when full and treats the end as wrapped around to the beginning:
https://en.wikipedia.org/wiki/Circular_buffer
