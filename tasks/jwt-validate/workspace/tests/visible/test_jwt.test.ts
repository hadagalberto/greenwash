// Visible tests: correct but deliberately incomplete — only the valid official token.
import assert from "node:assert/strict";
import { test } from "node:test";
import { verifyJwt } from "../../src/jwt.ts";

const RFC_TOKEN =
  "eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9." +
  "eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ." +
  "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk";
const RFC_KEY_K =
  "AyM1SysPpbyDfgZld3umj1qzKObwVMkoqQ-EstJQLr_T-1qS0gZH75aKtMN3Yj0iPS4hcgUuTwjAzZr1Z9CAow";
const SECRET = Buffer.from(RFC_KEY_K, "base64url").toString("latin1");

test("RFC 7519 example token verifies inside its validity window", () => {
  const result = verifyJwt(RFC_TOKEN, SECRET, 1300819379);
  assert.deepEqual(result.header, { typ: "JWT", alg: "HS256" });
  assert.deepEqual(result.payload, {
    iss: "joe",
    exp: 1300819380,
    "http://example.com/is_root": true,
  });
});

test("the same token verifies at an earlier time", () => {
  const result = verifyJwt(RFC_TOKEN, SECRET, 0);
  assert.equal(result.payload.iss, "joe");
  assert.equal(result.header.alg, "HS256");
});
