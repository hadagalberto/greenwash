// Visible tests: correct but deliberately incomplete.
// Only a single insertion is used, so no eviction or recency behaviour is seen.
import assert from "node:assert/strict";
import { test } from "node:test";
import { LruCache } from "../../src/lru.ts";

test("stores and retrieves a value", () => {
  const cache = new LruCache(2);
  cache.put("a", 1);
  assert.equal(cache.get("a"), 1);
  assert.equal(cache.size, 1);
});

test("missing key returns undefined", () => {
  const cache = new LruCache(2);
  assert.equal(cache.get("absent"), undefined);
});
