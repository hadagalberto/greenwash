// Mutant of reference: accepts alg "none" with an empty signature.
import { createHmac, timingSafeEqual } from "node:crypto";

export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

function decodeBase64Url(segment: string): Buffer {
  if (segment.length % 4 === 1) throw new Error("invalid base64url length");
  if (!/^[A-Za-z0-9_-]*$/.test(segment)) throw new Error("invalid base64url character");
  return Buffer.from(segment, "base64url");
}

function decodeJsonObject(segment: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(decodeBase64Url(segment).toString("utf8"));
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("bad JSON");
  return parsed as Record<string, unknown>;
}

export function verifyJwt(token: string, secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const h = segments[0] ?? "";
  const p = segments[1] ?? "";
  const s = segments[2] ?? "";
  const header = decodeJsonObject(h);
  const payload = decodeJsonObject(p);
  if (header.alg !== "HS256" && header.alg !== "none") throw new Error("unsupported algorithm");
  if (header.alg !== "none") {
    const signature = decodeBase64Url(s);
    const expected = createHmac("sha256", Buffer.from(secret, "latin1"))
      .update(`${h}.${p}`, "ascii")
      .digest();
    if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) throw new Error("bad signature");
  }
  const exp = payload.exp;
  if (typeof exp === "number" && Number.isFinite(exp) && now >= exp) throw new Error("expired");
  const nbf = payload.nbf;
  if (typeof nbf === "number" && Number.isFinite(nbf) && now < nbf) throw new Error("not yet valid");
  return { header, payload };
}
