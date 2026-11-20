# LRU cache

Implement `src/lru.ts` exporting a class with this exact API:

```ts
export class LruCache {
  constructor(capacity: number);
  get(key: string): number | undefined;
  put(key: string, value: number): void;
  readonly size: number; // getter
}
```

Keys are strings, values are numbers. Behaviour must be fully deterministic.

## Constructor

`capacity` must be a non-negative integer (`Number.isInteger(capacity) &&
capacity >= 0`). Otherwise throw `RangeError`.

## Operations

- `get(key)`: returns the stored value, or `undefined` if the key is absent.
  A **hit refreshes recency**: the key becomes the most recently used entry.
  A miss does not change the cache.
- `put(key, value)`: inserts a new key or updates an existing key's value.
  An update also refreshes recency. After an insert that makes the entry count
  exceed `capacity`, evict exactly the **least recently used** entry (the one
  whose last access — insert, update or get — is oldest). Only one entry is
  evicted per insert.
- `capacity === 0`: `put` is a no-op; `get` always returns `undefined`;
  `size` is always `0`.
- `size`: current number of stored entries.

Ordering is by **use time**, not insertion time. A `get` on an old key makes it
the most recently used key, so a subsequent eviction must remove a different
key than it would have before that `get`.

Worked examples (all must hold):

```ts
const c = new LruCache(2);
c.put("a", 1);
c.put("b", 2);
c.get("a");            // 1 — refreshes "a"
c.put("c", 3);         // evicts "b", not "a"
c.get("b");            // undefined
c.get("a");            // 1
c.get("c");            // 3
c.size;                // 2

const u = new LruCache(2);
u.put("a", 1);
u.put("b", 2);
u.put("a", 10);        // update refreshes "a"
u.put("c", 3);         // evicts "b"
u.get("a");            // 10
u.get("b");            // undefined
u.size;                // 2

const z = new LruCache(0);
z.put("a", 1);
z.get("a");            // undefined
z.size;                // 0

new LruCache(-1);      // throws RangeError
new LruCache(1.5);     // throws RangeError
```

## Source (fetched 2026-11-20)

Wikipedia, "Cache replacement policies", section "Least Recently Used (LRU)":
LRU "discards least recently used items first"; on an access the item's rank is
updated, and on a miss the new item replaces the lowest-rank (least recently
used) entry. Contrast with FIFO, which evicts in insertion order regardless of
accesses: https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)
