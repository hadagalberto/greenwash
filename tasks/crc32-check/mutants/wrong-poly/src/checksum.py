"""CRC-32 over arbitrary bytes.

Algorithm and polynomial from RFC 1952 Appendix 8:
https://www.rfc-editor.org/rfc/rfc1952.txt
"""

_POLYNOMIAL = 0x82F63B78
_MASK = 0xFFFFFFFF


def _make_table() -> tuple[int, ...]:
    table: list[int] = []
    for index in range(256):
        value = index
        for _ in range(8):
            value = (_POLYNOMIAL ^ (value >> 1)) if value & 1 else value >> 1
        table.append(value & _MASK)
    return tuple(table)


_TABLE = _make_table()


def crc32(data: bytes) -> int:
    """Return the CRC-32 of ``data`` as an unsigned 32-bit integer."""
    crc = _MASK
    for byte in data:
        crc = _TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return (crc ^ _MASK) & _MASK
