// Skeleton: splits on '=' but does no decoding.
export function parseQuery(query: string): Record<string, string | string[]> {
  const result: Record<string, string | string[]> = {};
  for (const segment of query.replace(/^\?/, '').split('&')) {
    const [key, value = ''] = segment.split('=');
    if (key) result[key] = value;
  }
  return result;
}
