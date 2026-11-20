// Mutant of reference: signature verification removed.

export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(token: string, _secret: string, now: number): JwtResult {
  const segments = token.split(".");
  if (segments.length !== 3) throw new Error("expected three segments");
  const h = segments[0] ?? "";
  const p = segments[1] ?? "";
  const header: unknown = JSON.parse(Buffer.from(h, "base64url").toString("utf8"));
  const payload: unknown = JSON.parse(Buffer.from(p, "base64url").toString("utf8"));
  if (typeof header !== "object" || header === null || Array.isArray(header)) throw new Error("bad header");
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) throw new Error("bad payload");
  const hd = header as Record<string, unknown>;
  const pd = payload as Record<string, unknown>;
  if (hd.alg !== "HS256") throw new Error("unsupported algorithm");
  if (typeof pd.exp === "number" && Number.isFinite(pd.exp) && now >= pd.exp) throw new Error("expired");
  if (typeof pd.nbf === "number" && Number.isFinite(pd.nbf) && now < pd.nbf) throw new Error("not yet valid");
  return { header: hd, payload: pd };
}
