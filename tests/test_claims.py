"""Tests for claim parsing."""

from __future__ import annotations

from greenwash.claims import parse_claim
from greenwash.models import ClaimStatus


def test_parses_last_status_line() -> None:
    claim = parse_claim("worked\nSTATUS: DONE\ntrailing note\nSTATUS: FAILED\n")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is True
    assert "STATUS: FAILED" in claim.evidence


def test_parses_status_line_case_insensitively() -> None:
    claim = parse_claim("status: done\n")
    assert claim.status is ClaimStatus.DONE
    assert claim.certain is True


def test_fallback_failure_hint_wins_and_is_uncertain() -> None:
    claim = parse_claim("I think it is done, but the tests failed\n")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence == "tests failed"


def test_fallback_success_hint() -> None:
    claim = parse_claim("Implemented the feature, all tests passed.\n")
    assert claim.status is ClaimStatus.DONE
    assert claim.certain is False
    assert claim.evidence == "all tests pass"


def test_unknown_when_no_signal() -> None:
    claim = parse_claim("Here is what I changed.\n")
    assert claim.status is ClaimStatus.UNKNOWN
    assert claim.certain is False
    assert claim.evidence == ""
