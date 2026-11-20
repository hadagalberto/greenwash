# Text wrapping with East Asian display width

Implement `src/wrap.ts` exporting exactly two functions:

```ts
export function displayWidth(ch: string): number;
export function wrapText(text: string, width: number): string[];
```

No external libraries. Use explicit code-point range tables in your source.

## `displayWidth(ch)`

Returns the number of fixed-pitch terminal columns occupied by the **first Unicode
code point** of `ch`. An empty string returns `0`. The result is determined by
checking these tables **in this order**:

1. **Zero-width table** (Unicode general categories Mn (nonspacing mark) and Me
   (enclosing mark), plus U+200D ZERO WIDTH JOINER). If the code point is in this
   table, return `0`.
2. **Wide table** (East Asian Width values **W** (Wide) and **F** (Fullwidth)). If
   the code point is in this table, return `2`.
3. Otherwise return `1` (East Asian Width values Na, A, H and N all count as one
   column here).

Zero-width table (inclusive code-point ranges):

```text
0300..036F 0483..0489 0591..05BD 05BF 05C1..05C2 05C4..05C5 05C7
0610..061A 064B..065F 0670 06D6..06DC 06DF..06E4 06E7..06E8 06EA..06ED
0711 0730..074A 07A6..07B0 07EB..07F3
0816..0819 081B..0823 0825..0827 0829..082D 0859..085B 08D3..08E1 08E3..0902
093A 093C 0941..0948 094D 0951..0957 0962..0963
0E31 0E34..0E3A 0E47..0E4E 0EB1 0EB4..0EBC 0EC8..0ECD
0F18..0F19 0F35 0F37 0F39 0F71..0F7E 0F80..0F84 0F86..0F87 0F8D..0F97
0F99..0FBC 0FC6 102D..1030 1032..1037 1039..103A 103D..103E 1058..1059
105E..1060 1071..1074 1082 1085..1086 108D 109D 135D..135F
1712..1714 1732..1734 1752..1753 1772..1773 17B4..17B5 17B7..17BD 17C6
17C9..17D3 17DD 180B..180D 1885..1886 18A9 1920..1922 1927..1928 1932 1939..193B
1A17..1A18 1A1B 1A56 1A58..1A5E 1A60 1A62 1A65..1A6C 1A73..1A7C 1A7F
1AB0..1AFF 1B00..1B03 1B34 1B36..1B3A 1B3C 1B42 1B6B..1B73 1B80..1B81
1BA2..1BA5 1BA8..1BA9 1BAB..1BAD 1BE6 1BE8..1BE9 1BED 1BEF..1BF1
1C2C..1C33 1C36..1C37 1CD0..1CD2 1CD4..1CE0 1CE2..1CE8 1CED 1CF4 1CF8..1CF9
1DC0..1DFF 200D 20D0..20FF 2CEF..2CF1 2D7F 2DE0..2DFF 302A..302F 3099..309A
A66F..A672 A674..A67D A69E..A69F A6F0..A6F1 A802 A806 A80B A825..A826
A8C4..A8C5 A8E0..A8F1 A926..A92D A947..A951 A980..A982 A9B3 A9B6..A9B9 A9BC
A9E5 AA29..AA2E AA31..AA32 AA35..AA36 AA43 AA4C AA7C AAB0 AAB2..AAB4
AAB7..AAB8 AABE..AABF AAC1 AAEC..AAED AAF6 ABE5 ABE8 ABED FB1E
FE00..FE0F FE20..FE2F FEFF FFF9..FFFB 101FD 102E0 10376..1037A
```

Wide table (inclusive code-point ranges):

```text
1100..115F 231A..231B 2329..232A 23E9..23EC 23F0 23F3 25FD..25FE
2614..2615 2648..2653 267F 2693 26A1 26AA..26AB 26BD..26BE 26C4..26C5
26CE 26D4 26EA 26F2..26F3 26F5 26FA 26FD 2705 270A..270B 2728 274C 274E
2753..2755 2757 2795..2797 27B0 27BF 2B1B..2B1C 2B50 2B55
2E80..303E 3041..33FF 3400..4DBF 4E00..9FFF A000..A4CF AC00..D7A3
F900..FAFF FE10..FE19 FE30..FE6F FF00..FF60 FFE0..FFE6
1F300..1F64F 1F900..1F9FF 20000..3FFFD
```

Examples: `displayWidth("A") === 1`, `displayWidth("漢") === 2`
(U+6F22), `displayWidth("\uFF21") === 2` (fullwidth A), `displayWidth("\u0301") === 0`
(combining acute), `displayWidth("\u20DD") === 0` (enclosing circle),
`displayWidth("\u200D") === 0` (ZWJ).

## Grapheme clusters

For hard-breaking, split a word into **grapheme clusters** (UAX #29 extended
grapheme clusters, simplified to the subset needed here): a cluster is one base
code point followed by zero or more continuation code points, where a
continuation code point is any code point in the zero-width table above (this
includes ZWJ). No other combining behaviour is modelled. A cluster is never
split. Its width is the sum of `displayWidth` of its code points, which for a
base-plus-marks cluster equals the width of the base.

## `wrapText(text, width)`

Throws `RangeError` if `width < 1`. Returns `[]` if `text` contains no tokens
after tokenization. Otherwise:

1. Tokenize with `text.split(/ +/)` and drop empty tokens. Runs of ASCII spaces
   collapse to a single separator; leading/trailing spaces produce no tokens.
   Only ASCII space (U+0020) is a separator.
2. Process tokens greedily into lines. Maintain the current line and its column
   width. For a token of width `w`:
   - if the current line is empty, start the line with the token;
   - else if `currentWidth + 1 + w <= width`, append `" " + token` (the `1`
     is the single separating space);
   - else flush the current line and start a new line with the token.
3. If a token's width `w > width`, hard-break it instead: flush any current
   line first, then accumulate whole grapheme clusters into chunks of at most
   `width` columns. Each full chunk is emitted as its own line. A cluster whose
   own width already exceeds `width` is emitted alone (clusters are atomic).
   The final leftover chunk becomes the current line, so later tokens may still
   be appended to it.
4. After all tokens, emit any non-empty current line.

Worked examples (all must hold):

```text
wrapText("hello world", 5)  == ["hello", "world"]
wrapText("a b c", 5)        == ["a b c"]      // exactly 5 columns
wrapText("a b c", 3)        == ["a b", "c"]
wrapText("a b", 3)          == ["a b"]
wrapText("a  b", 3)         == ["a b"]     // space run collapsed
wrapText("   ", 5)          == []          // no tokens
wrapText("漢字", 2)          == ["漢", "字"] // two wide chars, width 2
wrapText("abc", 2)          == ["ab", "c"]
wrapText("e\u0301x", 1)      == ["e\u0301", "x"] // mark stays with base
wrapText("漢\u0301", 1)      == ["漢\u0301"]     // cluster atomic though 2 > 1
wrapText("", 5)             == []
wrapText("a", 0)            throws RangeError
```

## Sources (fetched 2026-11-20)

- UAX #11 East Asian Width, Revision 46, Unicode 18.0.0, dated 2026-07-31 —
  definitions ED2–ED7 (F, H, W, Na, A, N), section 5 (wide = one Em ≈ 2 columns,
  narrow = 1/2 Em ≈ 1 column), section 6.2 (nonspacing marks have no advance
  width): https://www.unicode.org/reports/tr11/
- UAX #29 Unicode Text Segmentation, Revision 49, Unicode 18.0.0, dated
  2026-09-01 — grapheme clusters are atomic user-perceived characters; rule GB9
  forbids a break before Extend or ZWJ: https://www.unicode.org/reports/tr29/
