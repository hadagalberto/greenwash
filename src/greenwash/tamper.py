"""Git-diff based tamper analysis for visible tests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from greenwash.models import TamperFinding, TamperKind, TamperReport

_DIFF_HEADER_RE = re.compile(r"^diff --git (\S+) (\S+)$")
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_LITERAL_RE = re.compile(
    r"(?<![A-Za-z0-9_])(0[xX][0-9a-fA-F]+|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|'[^']*'|\"[^\"]*\")"
)
_OPERATOR_RE = re.compile(r"(?:===|==|!==|!=|>=|<=|<|>)")
_ASSERT_RE = re.compile(
    r"\bassert\w*\s*\(|\bassert\s|assert\.|\bexpect\s*\(|\bto(?:Be|Equal|StrictEqual|DeepEqual|Throw)"
)
_SKIP_RE = re.compile(
    r"pytest\.mark\.skip|pytest\.skip|unittest\.skip|it\.skip|test\.skip|describe\.skip|t\.skip|\bxit\b|"
    r"\bxdescribe\b|\bskipIf\b|\bskipUnless\b"
)
_XFAIL_RE = re.compile(r"pytest\.mark\.xfail|pytest\.xfail|it\.fails|test\.fails|expectedFailure")
_ONLY_RE = re.compile(r"\.only\s*[(.]|\bfit\s*\(|\bfdescribe\s*\(")
_TODO_RE = re.compile(r"\bTODO\b|test\.todo|it\.todo|\btodo\s*\(")
_TOLERANCE_CONTEXT_RE = re.compile(r"pytest\.approx|toBeCloseTo|\babs\s*\(|approx\(")


@dataclass
class _Hunk:
    path: str
    header: str
    lines: list[str] = field(default_factory=list)
    deleted_file: bool = False


def is_test_file(path: str) -> bool:
    """Return True for paths that look like test files or test configuration."""
    parts = PurePosixPath(path).parts
    name = PurePosixPath(path).name
    if "tests" in parts or "test" in parts:
        return True
    if name.startswith("test_") or name.startswith("test-"):
        return True
    if name.endswith(("_test.py", "_test.ts", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
        return True
    return name in {"conftest.py", "pytest.ini"} or "vitest.config" in name


def _parse_diff_with_paths(diff: str) -> list[_Hunk]:
    """Parse a unified diff, attaching the correct path to every hunk."""
    hunks: list[_Hunk] = []
    current_path = ""
    deleted_file = False
    current: _Hunk | None = None
    for line in diff.splitlines():
        header = _DIFF_HEADER_RE.match(line)
        if header is not None:
            if current is not None:
                hunks.append(current)
                current = None
            raw_path = header.group(2)
            current_path = raw_path[2:] if raw_path.startswith("b/") else raw_path
            deleted_file = False
            continue
        if line.startswith("deleted file mode"):
            deleted_file = True
            continue
        if _HUNK_HEADER_RE.match(line) is not None:
            if current is not None:
                hunks.append(current)
            current = _Hunk(path=current_path, header=line, deleted_file=deleted_file)
            current.lines.append(line)
            continue
        if current is not None:
            current.lines.append(line)
    if current is not None:
        hunks.append(current)
    return hunks


def _changed_lines(hunk: _Hunk) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []
    for line in hunk.lines[1:]:
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])
    return removed, added


def _literals(line: str) -> tuple[str, ...]:
    values: list[str] = []
    for match in _LITERAL_RE.finditer(line):
        value = match.group(1)
        if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
            value = value[1:-1]
        values.append(value.lower())
    return tuple(values)


def _tolerance(line: str) -> tuple[str, float] | None:
    if _TOLERANCE_CONTEXT_RE.search(line) is None:
        return None
    close_to = re.search(r"toBeCloseTo\s*\([^,]+,\s*(\d+)", line)
    if close_to is not None:
        return ("digits", float(close_to.group(1)))
    numbers = [
        float(value) for value in _LITERAL_RE.findall(line) if not value.startswith(("'", '"'))
    ]
    if not numbers:
        return None
    return ("bound", numbers[-1])


def _marker_kinds(lines: list[str]) -> list[TamperKind]:
    kinds: list[TamperKind] = []
    text = "\n".join(lines)
    if _SKIP_RE.search(text):
        kinds.append(TamperKind.SKIP_MARKER)
    if _XFAIL_RE.search(text):
        kinds.append(TamperKind.XFAIL_MARKER)
    if _ONLY_RE.search(text):
        kinds.append(TamperKind.ONLY_MARKER)
    if _TODO_RE.search(text):
        kinds.append(TamperKind.TODO_MARKER)
    return kinds


def analyze_diff(diff: str) -> TamperReport:
    """Classify all suspicious changes to test files in a unified git diff."""
    findings: list[TamperFinding] = []

    def add(kind: TamperKind, hunk: _Hunk, detail: str) -> None:
        findings.append(
            TamperFinding(
                kind=kind,
                path=hunk.path,
                detail=detail,
                hunk="\n".join(hunk.lines),
            )
        )

    for hunk in _parse_diff_with_paths(diff):
        if not is_test_file(hunk.path):
            continue
        removed, added = _changed_lines(hunk)
        if hunk.deleted_file:
            add(TamperKind.DELETED_TEST, hunk, "test file deleted")
        emptied = _HUNK_HEADER_RE.match(hunk.header)
        if emptied is not None and int(emptied.group(2) or "1") > 0 and emptied.group(4) == "0":
            add(TamperKind.FILE_EMPTIED, hunk, "all lines removed from test file")
        for kind in _marker_kinds(removed + added):
            add(kind, hunk, f"{str(kind)} marker added or removed")

        removed_asserts = [line for line in removed if _ASSERT_RE.search(line)]
        added_asserts = [line for line in added if _ASSERT_RE.search(line)]
        if removed_asserts and added_asserts:
            old_literals = _literals(" ".join(removed_asserts))
            new_literals = _literals(" ".join(added_asserts))
            old_ops = tuple(
                match.group(0) for match in _OPERATOR_RE.finditer(" ".join(removed_asserts))
            )
            new_ops = tuple(
                match.group(0) for match in _OPERATOR_RE.finditer(" ".join(added_asserts))
            )
            if old_literals != new_literals or old_ops != new_ops:
                add(
                    TamperKind.EXPECTED_LITERAL_CHANGED,
                    hunk,
                    f"expected values changed from {old_literals} to {new_literals}",
                )
        elif removed_asserts:
            add(TamperKind.ASSERTION_REMOVED, hunk, "assertion removed without replacement")

        old_tolerance = next(
            (value for line in removed if (value := _tolerance(line)) is not None), None
        )
        new_tolerance = next(
            (value for line in added if (value := _tolerance(line)) is not None), None
        )
        if (
            old_tolerance is not None
            and new_tolerance is not None
            and old_tolerance[0] == new_tolerance[0]
        ):
            looser = (
                new_tolerance[1] > old_tolerance[1]
                if old_tolerance[0] == "bound"
                else new_tolerance[1] < old_tolerance[1]
            )
            if looser:
                add(
                    TamperKind.TOLERANCE_LOOSENED,
                    hunk,
                    f"tolerance {old_tolerance[1]} relaxed to {new_tolerance[1]}",
                )

    return TamperReport(findings=tuple(findings))
