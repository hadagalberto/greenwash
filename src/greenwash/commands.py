"""Test command execution with timeouts and output parsing."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from greenwash.models import Language, TestOutcome

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PYTEST_COUNTS = (
    ("passed", re.compile(r"(\d+)\s+passed\b")),
    ("failed", re.compile(r"(\d+)\s+failed\b")),
    ("skipped", re.compile(r"(\d+)\s+skipped\b")),
    ("error", re.compile(r"(\d+)\s+error(?:s)?\b")),
    ("xfailed", re.compile(r"(\d+)\s+xfailed\b")),
    ("xpassed", re.compile(r"(\d+)\s+xpassed\b")),
)
# node:test prints lines like "ℹ pass 3". Match any non-ASCII prefix explicitly:
# U+2139 is classified as a word character by some Unicode database versions.
_NODE_COUNTS = (
    ("passed", re.compile(r"^[^A-Za-z0-9]*pass\s+(\d+)\s*$", re.MULTILINE)),
    ("failed", re.compile(r"^[^A-Za-z0-9]*fail\s+(\d+)\s*$", re.MULTILINE)),
    ("skipped", re.compile(r"^[^A-Za-z0-9]*skipped\s+(\d+)\s*$", re.MULTILINE)),
    ("todo", re.compile(r"^[^A-Za-z0-9]*todo\s+(\d+)\s*$", re.MULTILINE)),
)


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _counts(text: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> dict[str, int]:
    result: dict[str, int] = {}
    for name, pattern in patterns:
        match = pattern.search(text)
        if match is not None:
            result[name] = int(match.group(1))
    return result


def _parse_pytest(text: str) -> tuple[int, int, int]:
    counts = _counts(text, _PYTEST_COUNTS)
    passed = counts.get("passed", 0) + counts.get("xpassed", 0)
    failed = counts.get("failed", 0) + counts.get("error", 0)
    skipped = counts.get("skipped", 0) + counts.get("xfailed", 0)
    return passed, failed, skipped


def _parse_node(text: str) -> tuple[int, int, int]:
    counts = _counts(text, _NODE_COUNTS)
    return (
        counts.get("passed", 0),
        counts.get("failed", 0),
        counts.get("skipped", 0) + counts.get("todo", 0),
    )


def _command_tokens(command: str) -> list[str]:
    tokens = shlex.split(command)
    if not tokens:
        raise ValueError("empty test command")
    # Keep commands portable: the leading `python` token resolves to the
    # interpreter that runs greenwash, even inside a fresh virtualenv.
    if tokens[0] == "python":
        tokens[0] = sys.executable
    return tokens


def run_tests(
    command: str,
    cwd: Path,
    timeout_s: int,
    language: Language,
    env_extra: dict[str, str] | None = None,
) -> TestOutcome:
    """Run a task's test command in ``cwd`` and parse its pass/fail counts."""
    env = dict(os.environ)
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(cwd),
            "PYTHONUTF8": "1",
            "NO_COLOR": "1",
            "FORCE_COLOR": "0",
        }
    )
    if env_extra:
        env.update(env_extra)

    stdout = ""
    stderr = ""
    returncode = 1
    timed_out = False
    try:
        completed = subprocess.run(
            _command_tokens(command),
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr) + f"\nTIMEOUT after {timeout_s}s"

    text = _strip_ansi(stdout + "\n" + stderr)
    parser = _parse_pytest if language is Language.PYTHON else _parse_node
    passed, failed, skipped = parser(text)
    if timed_out:
        failed = max(failed, 1)
    total = passed + failed + skipped
    return TestOutcome(
        command=command,
        returncode=returncode,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )
