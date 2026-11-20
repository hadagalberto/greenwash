// Unicode folding for slug generation.
export function foldText(input: string): string {
  if (typeof input !== 'string') throw new TypeError('input must be a string');
  return input.normalize('NFKD').toLowerCase();
}
