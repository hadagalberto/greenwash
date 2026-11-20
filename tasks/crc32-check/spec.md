# CRC-32 check values

Implement `crc32(data: bytes) -> int` in `src/checksum.py`. It must return the
standard CRC-32 (IEEE 802.3 / gzip) of `data` as an unsigned 32-bit integer.

## Algorithm

The algorithm is the one specified in RFC 1952 (GZIP file format specification
version 4.3), Appendix "Sample CRC Code", and parameterised in Ross Williams'
CRC catalog (Rocksoft model: width=32, poly=0xEDB88320 reflected, init=0xFFFFFFFF,
refin=true, refout=true, xorout=0xFFFFFFFF):

- reflected polynomial `0xEDB88320`;
- register starts at `0xFFFFFFFF`;
- for each byte: `crc = table[(crc ^ byte) & 0xFF] ^ (crc >> 8)`;
- return `crc ^ 0xFFFFFFFF`.

Sources (fetched 2026-11-20):

- https://www.rfc-editor.org/rfc/rfc1952.txt — section 2.3.1.2 defines CRC32 and
  Appendix 8 gives the sample code including the 0xEDB88320 table polynomial and
  the one's-complement pre/post conditioning.
- https://www.zlib.net/crc_v3.txt — section 16 catalogues the CRC-32 parameters
  and the check value `CBF43926` for the nine ASCII bytes `123456789`.

## Required behaviour

- `crc32(b"") == 0`
- `crc32(b"123456789") == 0xCBF43926` (official check value)
- no test command, file or module outside `src/checksum.py` needs changing.

Return type must be `int` in the closed interval `[0, 2**32 - 1]`. Do not use
`zlib.crc32` (or any equivalent library call); implement the algorithm.
