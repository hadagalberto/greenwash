// Skeleton: lowercases and replaces spaces only.
import { foldText } from './normalize.ts';

export function slugify(input: string): string {
  return foldText(input).toLowerCase().replace(/ /g, '-');
}
