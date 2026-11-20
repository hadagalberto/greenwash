// Mutant of reference: no strict base64url alphabet/length validation.
import { createHmac, timingSafeEqual } from "node:crypto";

export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(token: string, secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const h = segments[0] ?? "";
  const p = segments[1] ?? "";
  const s = segments[2] ?? "";
  const header: unknown = JSON.parse(Buffer.from(h, "base64url").toString("utf8"));
  const payload: unknown = JSON.parse(Buffer.from(p, "base64url").toString("utf8"));
  if (typeof header !== "object" || header === null || Array.isArray(header)) throw new Error("bad header");
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) throw new Error("bad payload");
  const hd = header as Record<string, unknown>;
  const pd = payload as Record<string, unknown>;
  if (hd.alg !== "HS256") throw new Error("unsupported algorithm");
  const signature = Buffer.from(s, "base64url");
  const expected = createHmac("sha256", Buffer.from(secret, "latin1"))
    .update(`${h}.${p}`, "ascii")
    .digest();
  if (signature.length !== expected.length || !timingSafeEqual(signature, expected)) throw new Error("bad signature");
  if (typeof pd.exp === "number" && Number.isFinite(pd.exp) && now >= pd.exp) throw new Error("expired");
  if (typeof pd.nbf === "number" && Number.isFinite(pd.nbf) && now < pd.nbf) throw new Error("not yet valid");
  return { header: hd, payload: pd };
}
