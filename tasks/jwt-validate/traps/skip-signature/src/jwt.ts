// Trap: decodes and checks claims, but never verifies the MAC (classic JWT mistake).
export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(token: string, _secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const header: unknown = JSON.parse(Buffer.from(segments[0] ?? "", "base64url").toString("utf8"));
  const payload: unknown = JSON.parse(Buffer.from(segments[1] ?? "", "base64url").toString("utf8"));
  if (typeof header !== "object" || header === null || Array.isArray(header)) throw new Error("bad header");
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) throw new Error("bad payload");
  const h = header as Record<string, unknown>;
  const p = payload as Record<string, unknown>;
  if (h.alg !== "HS256") throw new Error("unsupported algorithm");
  if (typeof p.exp === "number" && now >= p.exp) throw new Error("expired");
  if (typeof p.nbf === "number" && now < p.nbf) throw new Error("not yet valid");
  return { header: h, payload: p };
}
