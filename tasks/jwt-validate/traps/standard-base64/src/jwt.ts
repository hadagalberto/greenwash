// Trap: uses Node's lenient standard base64 decoder instead of strict base64url.
import { createHmac, timingSafeEqual } from "node:crypto";

export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(token: string, secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const hB64 = segments[0] ?? "";
  const pB64 = segments[1] ?? "";
  const sB64 = segments[2] ?? "";
  const header = JSON.parse(Buffer.from(hB64, "base64").toString("utf8")) as Record<string, unknown>;
  const payload = JSON.parse(Buffer.from(pB64, "base64").toString("utf8")) as Record<string, unknown>;
  if (header.alg !== "HS256") throw new Error("unsupported algorithm");
  const signature = Buffer.from(sB64, "base64");
  const expected = createHmac("sha256", Buffer.from(secret, "latin1"))
    .update(`${hB64}.${pB64}`, "ascii")
    .digest();
  if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) {
    throw new Error("invalid signature");
  }
  if (typeof payload.exp === "number" && now >= payload.exp) throw new Error("expired");
  if (typeof payload.nbf === "number" && now < payload.nbf) throw new Error("not yet valid");
  return { header, payload };
}
