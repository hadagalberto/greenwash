// Safe join: RFC 3986 §5.2.4 dot-segment normalization + OWASP traversal defenses.
export function safeJoin(base: string, userPath: string): string | null {
  if (base.includes("\u0000") || userPath.includes("\u0000")) return null;
  if (userPath === "") return null;
  if (userPath.startsWith("/")) return null;

  const segments: string[] = [];
  for (const part of base.split(/[\\/]+/)) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      segments.pop();
      continue;
    }
    segments.push(part);
  }

  let userDepth = 0;
  for (const part of userPath.split(/[\\/]+/)) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      if (userDepth === 0) return null;
      userDepth -= 1;
      segments.pop();
      continue;
    }
    segments.push(part);
    userDepth += 1;
  }
  return "/" + segments.join("/");
}
