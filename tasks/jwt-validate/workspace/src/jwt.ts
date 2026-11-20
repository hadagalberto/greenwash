// HS256 JWT verifier (incomplete starting point).

export interface JwtResult {
  header: Record<string, unknown>;
  payload: Record<string, unknown>;
}

export function verifyJwt(_token: string, _secret: string, _now: number): JwtResult {
  throw new Error("not implemented");
}
