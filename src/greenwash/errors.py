"""Shared adapter errors (kept separate so adapters can import each other safely)."""

from __future__ import annotations


class AdapterUnavailableError(RuntimeError):
    """Raised when a requested adapter is not installed or not configured."""
