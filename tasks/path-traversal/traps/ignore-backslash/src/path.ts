// Trap: handles dot segments but treats backslash as an ordinary filename character.
export function safeJoin(base: string, userPath: string): string | null {
  if (!userPath || userPath.includes("\u0000")) return null;
  if (userPath.startsWith("/") || /^[A-Za-z]:/.test(userPath)) return null;

  const segments = base.split("/").filter((part) => part !== "" && part !== ".");
  let depth = 0;
  for (const part of userPath.split("/")) {
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
