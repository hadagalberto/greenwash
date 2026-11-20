// Trap: checks the raw concatenated string with startsWith(base) — no normalization.
export function safeJoin(base: string, userPath: string): string | null {
  const joined = `${base}/${userPath}`.replace(/\\/g, "/").replace(/\/{2,}/g, "/");
  return joined.startsWith(`${base}/`) ? joined : null;
}
