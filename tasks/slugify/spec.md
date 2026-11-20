# Slug generation

Implement `src/normalize.ts` and `src/slug.ts`.

## `src/normalize.ts`

`foldText(input: string): string`: reject non-strings with `TypeError`; return
`input.normalize('NFKD')` with every character in Unicode general category
`M` removed (use the `\p{M}` regular-expression class with the `u` flag),
then lowercased.

## `src/slug.ts`

`slugify(input: string): string`: call `foldText`, replace every run of
characters outside `[a-z0-9]` with a single `-`, then remove leading and
trailing `-`. An empty result (or input with no ASCII alphanumerics) is `''`.

## Examples

```
slugify('Hello World')       === 'hello-world'
slugify('  A.B.C  ')         === 'a-b-c'
slugify('Café')              === 'cafe'
slugify('crème brûlée')      === 'creme-brulee'
slugify('Über')              === 'uber'
slugify('a__b')              === 'a-b'
slugify('日本語')             === ''
```

## Source (fetched 2026-11-20)

Unicode Standard Annex #15, Unicode Normalization Forms: NFKD applies
canonical and compatibility decompositions; combining marks remain as
separate code points that can be stripped:
https://www.unicode.org/reports/tr15/
