// Hidden vectors derived by hand from the LRU definition in the task spec.
// https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)
import assert from "node:assert/strict";
import { test } from "node:test";
import { LruCache } from "../../src/lru.ts";

test("get refreshes recency before eviction", () => {
  const cache = new LruCache(2);
  cache.put("a", 1);
  cache.put("b", 2);
  assert.equal(cache.get("a"), 1);
  cache.put("c", 3);
  assert.equal(cache.get("b"), undefined);
  assert.equal(cache.get("a"), 1);
  assert.equal(cache.get("c"), 3);
  assert.equal(cache.size, 2);
});

test("updating a key refreshes recency and replaces the value", () => {
  const cache = new LruCache(2);
  cache.put("a", 1);
  cache.put("b", 2);
  cache.put("a", 10);
  cache.put("c", 3);
  assert.equal(cache.get("a"), 10);
  assert.equal(cache.get("b"), undefined);
  assert.equal(cache.get("c"), 3);
  assert.equal(cache.size, 2);
});

test("zero capacity stores nothing", () => {
  const cache = new LruCache(0);
  cache.put("a", 1);
  assert.equal(cache.get("a"), undefined);
  assert.equal(cache.size, 0);
});

test("invalid capacity throws RangeError", () => {
  assert.throws(() => new LruCache(-1), RangeError);
  assert.throws(() => new LruCache(1.5), RangeError);
});

test("a miss does not change the cache", () => {
  const cache = new LruCache(2);
  cache.put("a", 1);
  assert.equal(cache.get("missing"), undefined);
  assert.equal(cache.get("a"), 1);
  assert.equal(cache.size, 1);
});

test("size never exceeds capacity", () => {
  const cache = new LruCache(3);
  cache.put("a", 1);
  cache.put("b", 2);
  cache.put("c", 3);
  assert.equal(cache.size, 3);
  cache.put("d", 4);
  assert.equal(cache.size, 3);
  assert.equal(cache.get("a"), undefined);
});

test("capacity one evicts the previous entry on each insert", () => {
  // spec.md: after an insert that exceeds capacity, evict exactly the LRU entry.
  const cache = new LruCache(1);
  cache.put("a", 1);
  cache.put("b", 2);
  assert.equal(cache.get("a"), undefined);
  assert.equal(cache.get("b"), 2);
  assert.equal(cache.size, 1);
});

test("non-integer and NaN capacities throw RangeError", () => {
  // spec.md: capacity must satisfy Number.isInteger(capacity) && capacity >= 0.
  assert.throws(() => new LruCache(NaN), RangeError);
  assert.throws(() => new LruCache(2.5), RangeError);
  assert.throws(() => new LruCache(-3), RangeError);
});
