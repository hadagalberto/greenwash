// URL-slug generation from folded text.
import { foldText } from './normalize.ts';

export function slugify(input: string): string {
  return foldText(input).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
