// Skeleton: treats every pointer as one literal key.
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export function parsePointer(pointer: string): string[] {
  return [pointer];
}
