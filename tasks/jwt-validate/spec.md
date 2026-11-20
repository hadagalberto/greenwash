# Verify an HS256 JWT (JWS Compact Serialization)

Implement `src/jwt.ts` exporting exactly:

```ts
export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(token: string, secret: string, now: number): JwtResult
```

`now` is an integer number of seconds since the Unix epoch, supplied by the
caller so validation is deterministic. On success return the decoded header and
payload objects. **Every failure must throw an `Error`.**

## Rules

1. **Structure.** `token` must be the JWS Compact Serialization: exactly three
   dot-separated segments `headerB64.payloadB64.signatureB64`. Two, four or any
   other number of segments is invalid. Header and payload segments must be
   non-empty.
2. **Base64url.** Each segment must use the unpadded base64url alphabet
   `[A-Za-z0-9_-]` only: reject `+`, `/`, `=`, whitespace and any other
   character, and reject a length congruent to 1 modulo 4. Decode header and
   payload segments as UTF-8 and parse them as JSON **objects** (not arrays,
   strings, numbers or null).
3. **Algorithm.** `header.alg` must be exactly the string `"HS256"`. Reject
   `"none"` (unsecured JWTs are not acceptable here) and every other value.
4. **Key.** The `secret` string is interpreted as raw bytes using ISO-8859-1
   (latin1): in Node, `Buffer.from(secret, "latin1")`. Each character code
   0–255 maps to one byte. The official test key below is supplied this way.
5. **Signature.** Compute `createHmac("sha256", keyBytes)` over the ASCII text
   `${headerB64}.${payloadB64}` (the JWS Signing Input). Base64url-decode the
   signature segment and compare it to the 32-byte MAC with
   `crypto.timingSafeEqual`; unequal lengths are a failure. An invalid MAC,
   including a signature produced with a different secret, must throw.
6. **Time claims.**
   - If `payload.exp` is present and is a finite JSON number, throw when
     `now >= exp` ("on or after" the expiration time).
   - If `payload.nbf` is present and is a finite JSON number, throw when
     `now < nbf` (before the not-before time).
   - An absent or non-numeric `exp`/`nbf` imposes no restriction. No clock-skew
     leeway is applied.
7. Any other parse/JSON/structure failure also throws.

## Official vector (RFC 7519 section 3.1, RFC 7515 Appendix A.1)

The RFC's example JWT (header `{"typ":"JWT","alg":"HS256"}`; payload
`{"iss":"joe","exp":1300819380,"http://example.com/is_root":true}`) is:

```text
eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ.dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

Its HMAC key is given in RFC 7515 Appendix A.1 as the JWK octet string
`k = "AyM1SysPpbyDfgZld3umj1qzKObwVMkoqQ-EstJQLr_T-1qS0gZH75aKtMN3Yj0iPS4hcgUuTwjAzZr1Z9CAow"`.
Decode `k` with base64url to obtain the 64 key bytes; tests pass those bytes as
a latin1 string as the `secret` argument. The token has `exp = 1300819380`, so
`now = 1300819379` is inside its validity window and `now = 1300819380` is
expired. The RFC signature (base64url) is
`dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk`; its standard-base64 spelling
`dBjftJeZ4CVP+mB92K27uhbUJU1p1r/wW1gFWFOEjXk` must be **rejected** because base64
characters are not valid base64url.

## Sources (fetched 2026-11-20)

- https://www.rfc-editor.org/rfc/rfc7519.txt — Section 3.1 gives the exact header,
  payload, encoded parts, signature and complete JWT used above; Section 4.1.4
  defines `exp` as "on or after which the JWT MUST NOT be accepted"; Section
  4.1.5 defines `nbf`; Section 7.2 lists the validation steps; Section 8 states
  HS256 is mandatory to implement.
- https://www.rfc-editor.org/rfc/rfc7515.txt — Section 2 defines base64url as
  URL-safe alphabet with all `=` padding omitted and the JWS Signing Input as
  `ASCII(BASE64URL(UTF8(header)) || '.' || BASE64URL(payload))`; Section 5.2
  defines MAC validation; Appendix A.1 gives the key and the MAC vector.
- https://www.rfc-editor.org/rfc/rfc7518.txt — Section 3.2: HS256 is HMAC using
  SHA-256 and the computed MAC must be compared to the decoded signature in a
  constant-time manner.
