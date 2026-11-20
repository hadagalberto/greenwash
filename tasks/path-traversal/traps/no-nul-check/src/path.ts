// Trap: otherwise correct but NUL bytes are passed through.
export function safeJoin(base: string, userPath: string): string | null {
  if (userPath === "") return null;
  if (/^[\\/]/.test(userPath) || /^[A-Za-z]:/.test(userPath)) return null;

  const segments: string[] = [];
  for (const part of base.split(/[\\/]+/)) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      segments.pop();
      continue;
    }
    segments.push(part);
  }

  let depth = 0;
  for (const part of userPath.split(/[\\/]+/)) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      if (depth === 0) return null;
      depth -= 1;
      segments.pop();
    } else {
      segments.push(part);
      depth += 1;
    }
  }
  return "/" + segments.join("/");
}
