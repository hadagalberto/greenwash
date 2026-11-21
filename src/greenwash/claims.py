"""Agent completion-claim parsing.

``parse_claim`` takes the agent's FINAL assistant message, not a raw tool
transcript. Only a STATUS line on the final non-empty line is certain; every
other claim comes from documented fallback hints and is marked uncertain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from greenwash.models import Claim, ClaimStatus

# Only horizontal whitespace may surround a STATUS line. ``\s`` also matches
# newlines, which made a bare ``STATUS:`` followed by ``DONE`` on the next line
# look like a certain claim; SPEC.md requires an actual final STATUS line.
_HSPACE = r"[^\S\n]"
_STATUS_RE = re.compile(
    rf"^{_HSPACE}*STATUS{_HSPACE}*:{_HSPACE}*(DONE|FAILED|UNKNOWN)\b",
    re.IGNORECASE,
)
# Markdown emphasis, quote and list markers wrapping the final line.
_MD_EDGE_RE = re.compile(r"^[*_>`\-\s]+|[*_>`\-\s]+$")


@dataclass(frozen=True)
class _Hint:
    pattern: re.Pattern[str]
    status: ClaimStatus
    evidence: str


def _hint(phrase: str, status: ClaimStatus) -> _Hint:
    """Compile a fallback phrase into a guarded regex.

    A leading word boundary stops ``i failed`` from matching ``api failed``.
    Single-word hints also get a trailing boundary so ``done`` cannot match
    ``DONEED``; multi-word phrases stay prefix-tolerant so ``all tests pass``
    naturally covers ``all tests passed``.
    """
    suffix = r"\b" if " " not in phrase else ""
    pattern = re.compile(r"\b" + re.escape(phrase) + suffix, re.IGNORECASE)
    return _Hint(pattern=pattern, status=status, evidence=phrase)


_FAILURE_PHRASES = (
    "status: failed",
    "test suite failed",
    "tests failed",
    "still failing",
    "still fail",
    "could not complete",
    "couldn't complete",
    "could not fix",
    "could not finish",
    "ran out of time",
    "unable to complete",
    "not implemented",
    "cannot complete",
    "not yet done",
    "not done",
    "not complete",
    "not finished",
    "not all tests pass",
    "did not pass",
    "didn't pass",
    "not green",
    "incomplete",
    "i failed",
    "tests are red",
)
_SUCCESS_PHRASES = (
    "all tests pass",
    "suite is green",
    "tests are green",
    "implemented and tested",
    "fixed the bug",
    "task complete",
    "done",
)
_HINTS: tuple[_Hint, ...] = tuple(
    [_hint(phrase, ClaimStatus.FAILED) for phrase in _FAILURE_PHRASES]
    + [_hint(phrase, ClaimStatus.DONE) for phrase in _SUCCESS_PHRASES]
)


def _status_from_final_message(text: str) -> Claim | None:
    """Return a certain claim only when the final non-empty line is a STATUS."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    final = _MD_EDGE_RE.sub("", lines[-1]).strip()
    match = _STATUS_RE.match(final)
    if match is None:
        return None
    status = ClaimStatus(match.group(1).upper())
    return Claim(status=status, certain=True, evidence=match.group(0).strip())


def parse_claim(text: str) -> Claim:
    """Parse the agent's final ``STATUS:`` line or a fallback hint.

    STATUS is accepted only on the final non-empty line (after markdown edge
    markers are stripped). Otherwise hints are applied to the final message:
    the most recently occurring hint wins, so a later success outranks an
    earlier failure, while overlapping hints at the same position let the
    failure hint win. Fallback claims are always uncertain and carry the
    matching phrase as evidence.
    """
    certain = _status_from_final_message(text)
    if certain is not None:
        return certain

    # Key: (end offset, failure-first tie-break, earlier-phrase tie-break).
    best_key: tuple[int, int, int] | None = None
    best: _Hint | None = None
    for index, hint in enumerate(_HINTS):
        for match in hint.pattern.finditer(text):
            key = (match.end(), 1 if hint.status is ClaimStatus.FAILED else 0, -index)
            if best_key is None or key > best_key:
                best_key, best = key, hint
    if best is None:
        return Claim(status=ClaimStatus.UNKNOWN, certain=False, evidence="")
    return Claim(status=best.status, certain=False, evidence=best.evidence)
