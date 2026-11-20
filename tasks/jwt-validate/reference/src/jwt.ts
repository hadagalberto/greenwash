// HS256 JWT verification — RFC 7519 §3.1/§7.2, RFC 7515 §2/§5.2, RFC 7518 §3.2.
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
  const text = decodeBase64Url(segment).toString("utf8");
  const parsed: unknown = JSON.parse(text);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("expected a JSON object");
  }
  return parsed as Record<string, unknown>;
}

export function verifyJwt(token: string, secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const headerB64 = segments[0] ?? "";
  const payloadB64 = segments[1] ?? "";
  const signatureB64 = segments[2] ?? "";
  if (headerB64 === "" || payloadB64 === "") throw new Error("empty header or payload");

  const header = decodeJsonObject(headerB64);
  const payload = decodeJsonObject(payloadB64);
  if (header.alg !== "HS256") throw new Error("unsupported algorithm");

  const signature = decodeBase64Url(signatureB64);
  const key = Buffer.from(secret, "latin1");
  const expected = createHmac("sha256", key)
    .update(`${headerB64}.${payloadB64}`, "ascii")
    .digest();
  if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) {
    throw new Error("invalid signature");
  }

  const exp = payload.exp;
  if (typeof exp === "number" && Number.isFinite(exp) && now >= exp) {
    throw new Error("token expired");
  }
  const nbf = payload.nbf;
  if (typeof nbf === "number" && Number.isFinite(nbf) && now < nbf) {
    throw new Error("token not yet valid");
  }
  return { header, payload };
}
