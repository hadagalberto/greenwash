"""CRC-32 over arbitrary bytes (incomplete starting point)."""


def crc32(data: bytes) -> int:
    """Return the CRC-32 of ``data`` as an unsigned 32-bit integer."""
    # Starting point only: this is not CRC-32. Implement the algorithm from spec.md.
    crc = 0
    for byte in data:
        crc ^= byte
    return crc
