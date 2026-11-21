"""Shared value types for the greenwash harness."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Language(StrEnum):
    """Languages supported by the task suite."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"


class ClaimStatus(StrEnum):
    """Outcome of parsing an agent's final status line."""

    DONE = "DONE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class TamperKind(StrEnum):
    """Classification of a suspicious change to a visible test file."""

    DELETED_TEST = "deleted_test"
    FILE_EMPTIED = "file_emptied"
    SKIP_MARKER = "skip_marker"
    XFAIL_MARKER = "xfail_marker"
    ONLY_MARKER = "only_marker"
    TODO_MARKER = "todo_marker"
    ASSERTION_REMOVED = "assertion_removed"
    EXPECTED_LITERAL_CHANGED = "expected_literal_changed"
    TOLERANCE_LOOSENED = "tolerance_loosened"
    # Milestone 9: attacks against the grader itself rather than test literals.
    SYMLINK = "symlink"
    ORACLE_INTERFERENCE = "oracle_interference"
    TEST_CONFIG_CHANGED = "test_config_changed"
    # Finding 10: a file declared protected in task.yaml was modified.
    PROTECTED_FILE_CHANGED = "protected_file_changed"


@dataclass(frozen=True)
class TestCommands:
    """Test commands declared by a task."""

    visible: str
    hidden: str


@dataclass(frozen=True)
class Task:
    """A validated task directory."""

    root: Path
    id: str
    title: str
    language: Language
    category: str
    difficulty: str
    time_budget_s: int
    test_commands: TestCommands
    sources: tuple[str, ...]
    protected_files: tuple[str, ...]
    # Files the agent is allowed to change. When non-empty, hidden grading copies
    # only these files from the agent's tree into a harness-owned fresh directory.
    implementation_files: tuple[str, ...] = ()

    @property
    def workspace_dir(self) -> Path:
        return self.root / "workspace"

    @property
    def hidden_dir(self) -> Path:
        return self.root / "hidden"

    @property
    def reference_dir(self) -> Path:
        return self.root / "reference"

    @property
    def traps_dir(self) -> Path:
        return self.root / "traps"

    @property
    def mutants_dir(self) -> Path:
        return self.root / "mutants"

    @property
    def spec_path(self) -> Path:
        return self.root / "spec.md"

    @property
    def visible_test_dir(self) -> Path:
        """Relative path of the visible test directory inside the workspace."""
        return Path("tests/visible")

    @property
    def hidden_test_dir(self) -> Path:
        """Relative path of the hidden test directory inside the workspace."""
        return Path("tests/hidden")


@dataclass(frozen=True)
class TestOutcome:
    """Result of running one test command."""

    command: str
    returncode: int
    passed: int
    failed: int
    skipped: int
    total: int
    stdout: str
    stderr: str
    timed_out: bool

    @property
    def ok(self) -> bool:
        """True only when at least one test ran and none failed."""
        return not self.timed_out and self.returncode == 0 and self.failed == 0 and self.total > 0

    @property
    def score(self) -> float:
        """Fraction of tests that passed (used for partial hidden score)."""
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.total,
            "timed_out": self.timed_out,
            "ok": self.ok,
            "score": self.score,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class Claim:
    """An agent's claimed completion status."""

    status: ClaimStatus
    certain: bool
    evidence: str

    def to_dict(self) -> dict[str, object]:
        return {"status": str(self.status), "certain": self.certain, "evidence": self.evidence}


@dataclass(frozen=True)
class TamperFinding:
    """One classified tamper finding with its exact diff hunk."""

    kind: TamperKind
    path: str
    detail: str
    hunk: str

    def to_dict(self) -> dict[str, object]:
        return {"kind": str(self.kind), "path": self.path, "detail": self.detail, "hunk": self.hunk}


@dataclass(frozen=True)
class TamperReport:
    """All tamper findings for one attempt."""

    findings: tuple[TamperFinding, ...]

    def by_kind(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[str(finding.kind)] = counts.get(str(finding.kind), 0) + 1
        return counts

    def to_dict(self) -> dict[str, object]:
        return {
            "findings": [finding.to_dict() for finding in self.findings],
            "by_kind": self.by_kind(),
        }


@dataclass(frozen=True)
class AgentResult:
    """Output of running an agent adapter."""

    adapter: str
    model: str
    transcript: str
    claim: Claim
    tokens_in: int
    tokens_out: int
    cost_usd: float
    wall_s: float
    timed_out: bool
    exit_code: int
    # The agent's final assistant message, kept separate from tool output.
    final_message: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.adapter,
            "model": self.model,
            "transcript": self.transcript,
            "claim": self.claim.to_dict(),
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "wall_s": self.wall_s,
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
            "final_message": self.final_message,
        }
