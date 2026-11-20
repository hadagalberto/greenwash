"""EAN-13 and UPC-A check digit helpers (incomplete starting point)."""


def ean13_check_digit(payload12: str) -> str:
    """Return the EAN-13 check digit for a 12-digit ``payload12``."""
    # Starting point only: implement the algorithm described in spec.md.
    return "0"


def is_valid_ean13(code: str) -> bool:
    """Return whether ``code`` is a 13-digit EAN-13 with a valid check digit."""
    # Starting point only: implement the algorithm described in spec.md.
    return False


def upca_check_digit(payload11: str) -> str:
    """Return the UPC-A check digit for an 11-digit ``payload11``."""
    # Starting point only: implement the algorithm described in spec.md.
    return "0"


def is_valid_upca(code: str) -> bool:
    """Return whether ``code`` is a 12-digit UPC-A with a valid check digit."""
    # Starting point only: implement the algorithm described in spec.md.
    return False
