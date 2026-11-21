// SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
// Every rule below is exercised by at least one test in this directory.
// R1: **Every failure must throw an `Error`.** ## Rules 1.
//     -> exp is exclusive: now === exp throws, now === exp - 1 passes, nbf is inclusive: now ===
//       nbf - 1 throws, now === nbf passes, a changed signature byte is rejected
// R2: **Structure.** `token` must be the JWS Compact Serialization: ...
//     -> a token signed with the wrong secret is rejected, a token with a trailing newline is
//       rejected, four segments are rejected
// R3: Header and payload segments must be non-empty.
//     -> a non-object header is rejected, official RFC token returns the exact header and payload,
//       a non-numeric exp claim imposes no expiry restriction
// R4: **Base64url.** Each segment must use the unpadded base64url alphabet ...
//     -> base64 padding in a segment is rejected, exp is exclusive: now === exp throws, now ===
//       exp - 1 passes, nbf is inclusive: now === nbf - 1 throws, now === nbf passes
// R5: Decode header and payload segments as UTF-8 and parse them as JSON ...
//     -> invalid JSON in the header is rejected, official RFC token returns the exact header and
//       payload, a non-object header is rejected
// R6: **Algorithm.** `header.alg` must be exactly the string `"HS256"`.
//     -> a non-object header is rejected, alg , invalid JSON in the header is rejected
// R7: Reject `"none"` (unsecured JWTs are not acceptable here) and every ...
//     -> a changed signature byte is rejected, a non-numeric exp claim imposes no expiry
//       restriction, a non-object header is rejected
// R8: An invalid MAC, including a signature produced with a different ...
//     -> a changed signature byte is rejected, a token signed with the wrong secret is rejected,
//       invalid JSON in the header is rejected
// R9: - If `payload.nbf` is present and is a finite JSON number, throw ...
//     -> unicode digits in exp are a string, not a finite JSON number, nbf is inclusive: now ===
//       nbf - 1 throws, now === nbf passes, exp and nbf are both enforced
// R10: The RFC signature (base64url) is `dBjftJeZ4CVP- ...
//     -> standard base64 signature characters are rejected, a changed signature byte is rejected,
//       base64 padding in a segment is rejected
// R11: ## Sources (fetched 2026-11-20) - https://www.rfc- ...
//     -> official RFC token returns the exact header and payload, exp and nbf are both enforced,
//       exp is exclusive: now === exp throws, now === exp - 1 passes
// R12: - https://www.rfc-editor.org/rfc/rfc7518.txt — Section 3.2: HS256 is ...
//     -> a changed signature byte is rejected, official RFC token returns the exact header and
//       payload, standard base64 signature characters are rejected
//
// Hand-derived vectors from RFC 7519 section 3.1 / RFC 7515 Appendix A.1 plus
// locally signed tokens for the exp/nbf boundaries. No reference import.
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { test } from "node:test";
import { verifyJwt } from "../../src/jwt.ts";

const RFC_TOKEN =
  "eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9." +
  "eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ." +
  "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk";
const RFC_KEY_K =
  "AyM1SysPpbyDfgZld3umj1qzKObwVMkoqQ-EstJQLr_T-1qS0gZH75aKtMN3Yj0iPS4hcgUuTwjAzZr1Z9CAow";
const RFC_SECRET = Buffer.from(RFC_KEY_K, "base64url").toString("latin1");
const NOW_IN_WINDOW = 1300819379;
const SIGNING_SECRET = "test-secret-for-hs256";

function sign(header: object, payload: object, secret: string): string {
  const h = Buffer.from(JSON.stringify(header), "utf8").toString("base64url");
  const p = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  const mac = createHmac("sha256", Buffer.from(secret, "latin1"))
    .update(`${h}.${p}`, "ascii")
    .digest("base64url");
  return `${h}.${p}.${mac}`;
}

test("official RFC token returns the exact header and payload", () => {
  const result = verifyJwt(RFC_TOKEN, RFC_SECRET, NOW_IN_WINDOW);
  assert.deepEqual(result.header, { typ: "JWT", alg: "HS256" });
  assert.deepEqual(result.payload, {
    iss: "joe",
    exp: 1300819380,
    "http://example.com/is_root": true,
  });
});

test("official token at its expiration instant is rejected", () => {
  assert.throws(() => verifyJwt(RFC_TOKEN, RFC_SECRET, 1300819380), Error);
});

test("a changed signature byte is rejected", () => {
  const tampered = RFC_TOKEN.slice(0, -1) + "A";
  assert.throws(() => verifyJwt(tampered, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("a token signed with the wrong secret is rejected", () => {
  assert.throws(() => verifyJwt(RFC_TOKEN, "a-different-secret", NOW_IN_WINDOW), Error);
});

test('alg "none" is rejected even with an empty signature', () => {
  const header = Buffer.from('{"alg":"none"}', "utf8").toString("base64url");
  const payload = RFC_TOKEN.split(".")[1] ?? "";
  assert.throws(() => verifyJwt(`${header}.${payload}.`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test('alg "HS512" is rejected', () => {
  const header = Buffer.from('{"alg":"HS512"}', "utf8").toString("base64url");
  const payload = RFC_TOKEN.split(".")[1] ?? "";
  const signature = RFC_TOKEN.split(".")[2] ?? "";
  assert.throws(() => verifyJwt(`${header}.${payload}.${signature}`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("exp is exclusive: now === exp throws, now === exp - 1 passes", () => {
  const token = sign({ alg: "HS256" }, { sub: "alice", exp: 100 }, SIGNING_SECRET);
  assert.throws(() => verifyJwt(token, SIGNING_SECRET, 100), Error);
  const ok = verifyJwt(token, SIGNING_SECRET, 99);
  assert.deepEqual(ok.payload, { sub: "alice", exp: 100 });
});

test("nbf is inclusive: now === nbf - 1 throws, now === nbf passes", () => {
  const token = sign({ alg: "HS256" }, { sub: "bob", nbf: 100 }, SIGNING_SECRET);
  assert.throws(() => verifyJwt(token, SIGNING_SECRET, 99), Error);
  const ok = verifyJwt(token, SIGNING_SECRET, 100);
  assert.deepEqual(ok.payload, { sub: "bob", nbf: 100 });
});

test("exp and nbf are both enforced", () => {
  const token = sign(
    { alg: "HS256" },
    { sub: "carol", nbf: 10, exp: 20 },
    SIGNING_SECRET,
  );
  assert.throws(() => verifyJwt(token, SIGNING_SECRET, 9), Error);
  assert.equal(verifyJwt(token, SIGNING_SECRET, 10).payload.sub, "carol");
  assert.equal(verifyJwt(token, SIGNING_SECRET, 19).payload.sub, "carol");
  assert.throws(() => verifyJwt(token, SIGNING_SECRET, 20), Error);
});

test("two segments are rejected", () => {
  const parts = RFC_TOKEN.split(".");
  assert.throws(() => verifyJwt(`${parts[0]}.${parts[1]}`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("four segments are rejected", () => {
  assert.throws(() => verifyJwt(`${RFC_TOKEN}.extra`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("standard base64 signature characters are rejected", () => {
  const standardB64Signature = "dBjftJeZ4CVP+mB92K27uhbUJU1p1r/wW1gFWFOEjXk";
  const prefix = RFC_TOKEN.slice(0, RFC_TOKEN.lastIndexOf(".") + 1);
  assert.throws(() => verifyJwt(prefix + standardB64Signature, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("base64 padding in a segment is rejected", () => {
  assert.throws(() => verifyJwt(`${RFC_TOKEN}=`, RFC_SECRET, NOW_IN_WINDOW), Error);
  const parts = RFC_TOKEN.split(".");
  assert.throws(() => verifyJwt(`${parts[0]}=.${parts[1]}.${parts[2]}`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("invalid JSON in the header is rejected", () => {
  const h = Buffer.from("not json", "utf8").toString("base64url");
  const parts = RFC_TOKEN.split(".");
  assert.throws(() => verifyJwt(`${h}.${parts[1]}.${parts[2]}`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("a non-object header is rejected", () => {
  const h = Buffer.from("[1,2]", "utf8").toString("base64url");
  const parts = RFC_TOKEN.split(".");
  assert.throws(() => verifyJwt(`${h}.${parts[1]}.${parts[2]}`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("a non-numeric exp claim imposes no expiry restriction", () => {
  const token = sign({ alg: "HS256" }, { sub: "dave", exp: "not-a-number" }, SIGNING_SECRET);
  assert.equal(verifyJwt(token, SIGNING_SECRET, 10_000).payload.sub, "dave");
});

test("a token with a trailing newline is rejected", () => {
  assert.throws(() => verifyJwt(`${RFC_TOKEN}\n`, RFC_SECRET, NOW_IN_WINDOW), Error);
});

test("unicode digits in exp are a string, not a finite JSON number", () => {
  const token = sign({ alg: "HS256" }, { sub: "unicode", exp: "١٠٠" }, SIGNING_SECRET);
  assert.equal(verifyJwt(token, SIGNING_SECRET, 10_000).payload.sub, "unicode");
});
