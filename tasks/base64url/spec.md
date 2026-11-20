# URL-safe unpadded base64

Implement `src/base64url.ts` exporting:

```ts
export function encodeUrl(data: Uint8Array): string;
export function decodeUrl(text: string): Uint8Array;
```

Use the **base64url** alphabet from RFC 4648 section 5: identical to base64 except
index 62 is `-` (minus) and index 63 is `_` (underline). Emit **no padding** (`=`)
and no line feeds. Decoding must reject any character outside the alphabet
(including `+`, `/`, `=` and whitespace) by throwing an `Error`, and reject a
length congruent to 1 modulo 4. Reject non-zero pad bits for canonical encoding.

Source (fetched 2026-11-20): https://www.rfc-editor.org/rfc/rfc4648.txt —
section 5 defines the URL and filename safe alphabet (Table 2), section 3.2
allows skipping padding when the data length is known implicitly, section 3.3
requires rejecting non-alphabet characters, section 3.5 requires zero pad bits.

## Official vectors

RFC 4648 section 10 gives base64 vectors; after applying the section 5 alphabet
substitution (`+` → `-`, `/` → `_`) and removing `=` padding they become:

| input bytes | base64 (RFC 4648 §10) | base64url (required) |
| --- | --- | --- |
| `""` | `""` | `""` |
| `"f"` | `Zg==` | `Zg` |
| `"fo"` | `Zm8=` | `Zm8` |
| `"foo"` | `Zm9v` | `Zm9v` |
| `0x14fb9c03d97e` | `FPucA9l+` | `FPucA9l-` |

Additional check: `encodeUrl(Uint8Array.of(0xfb, 0xff, 0x00)) === "-_8A"`
(the RFC illustration's base64 `+/8A` with the URL-safe alphabet and no padding).

Do not use Node's `Buffer` base64 helpers; implement the codec.
