"""Test command execution with timeouts and output parsing."""

from __future__ import annotations

import os
import re
import shlex
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from greenwash.models import Language, TestOutcome
from greenwash.sandbox import LocalSandbox, Sandbox

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

# Environment variables an agent could use to alter the hidden test run.  They
# are removed before the harness-owned hidden command is assembled.
_HOSTILE_ENV = (
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONSTARTUP",
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTEST_CURRENT_TEST",
)

# Freezing node's assert module stops an implementation file from replacing
# assertion functions at import time.  Loaded via `node --import` before tests.
_NODE_FREEZE_ASSERT = """
import assert from 'node:assert/strict';
try { Object.freeze(assert); } catch {}
"""


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


def _parse_junit(path: Path) -> tuple[int, int, int] | None:
    """Read authoritative counts from a harness-owned JUnit XML report.

    Pytest emits ``testsuite`` elements carrying ``tests``/``failures``
    attributes; node:test emits ``testcase`` elements directly under
    ``testsuites``.  Both shapes are handled because the report, not stdout,
    is the oracle.
    """
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return None
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    declared = [suite for suite in suites if suite.get("tests") is not None]
    if declared:
        total = sum(int(suite.get("tests", "0")) for suite in declared)
        skipped = sum(int(suite.get("skipped", "0")) for suite in declared)
        failed = sum(int(suite.get("failures", "0")) for suite in declared) + sum(
            int(suite.get("errors", "0")) for suite in declared
        )
    else:
        cases = list(root.iter("testcase"))
        total = len(cases)
        skipped = sum(
            1
            for case in cases
            if case.get("skipped") is not None or case.find("skipped") is not None
        )
        failed = sum(
            1
            for case in cases
            if case.get("failure") is not None
            or case.get("error") is not None
            or case.find("failure") is not None
            or case.find("error") is not None
        )
    if total == 0:
        return None
    return max(0, total - failed - skipped), failed, skipped


def _unquote(token: str) -> str:
    """Strip one matching pair of quotes left by POSIX-incompatible shlex mode."""
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def _command_tokens(
    command: str, native_python: bool = True, *, posix: bool | None = None
) -> list[str]:
    """Split a test command into argv tokens.

    ``shlex``'s POSIX mode treats ``\\`` as an escape character, which silently
    destroys Windows paths such as ``tests\\visible``. On Windows use the
    non-POSIX mode (which preserves backslashes) and remove the surrounding
    quotes it keeps on quoted arguments. ``posix`` is explicit so this behaviour
    is testable on every platform; ``None`` selects the host convention.
    """
    if posix is None:
        posix = os.name != "nt"
    if posix:
        tokens = shlex.split(command)
    else:
        tokens = [_unquote(token) for token in shlex.split(command, posix=False)]
    if not tokens:
        raise ValueError("empty test command")
    # On the host, `python` resolves to the interpreter running greenwash.
    # Inside a container that path does not exist, so keep the bare name.
    if native_python and tokens[0] == "python":
        tokens[0] = sys.executable
    return tokens


def _hidden_env(fresh_dir: Path, native_python: bool) -> dict[str, str]:
    """Harness-controlled environment for the hidden run (CI root cause A)."""
    env: dict[str, str] = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONPATH": str(fresh_dir) if native_python else "/work",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
    }
    for name in _HOSTILE_ENV:
        env[name] = ""
    return env


def run_tests(
    command: str,
    cwd: Path,
    timeout_s: int,
    language: Language,
    env_extra: dict[str, str] | None = None,
    sandbox: Sandbox | None = None,
) -> TestOutcome:
    """Run a task's test command in ``cwd`` and parse its pass/fail counts."""
    backend = sandbox or LocalSandbox()
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONPATH": str(cwd) if backend.native_python else "/work",
        "PYTHONUTF8": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
    }
    if env_extra:
        env.update(env_extra)

    output = backend.run_argv(
        _command_tokens(command, backend.native_python), cwd, timeout_s, env_extra=env
    )
    stdout, stderr = output.stdout, output.stderr
    returncode = output.returncode
    timed_out = output.timed_out
    if timed_out:
        stderr += f"\nTIMEOUT after {timeout_s}s"

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


def run_hidden_tests(
    command: str,
    fresh_dir: Path,
    timeout_s: int,
    language: Language,
    *,
    junit_path: Path,
    config_path: Path,
    preload_path: Path | None = None,
    sandbox: Sandbox | None = None,
) -> TestOutcome:
    """Run hidden tests in a harness-owned directory with a trusted oracle.

    Both frameworks are invoked with a report file OUTSIDE the agent's tree,
    so a hostile implementation cannot fake a pass by rewriting stdout.  The
    configuration and node preload are also harness-owned.
    """
    backend = sandbox or LocalSandbox()
    env = _hidden_env(fresh_dir, backend.native_python)
    if language is Language.PYTHON:
        python = sys.executable if backend.native_python else "python"
        # -E ignores every PYTHON* variable (including a hostile PYTHONPATH),
        # while still keeping the interpreter's own site-packages so pytest can
        # be imported.  The harness ini supplies the fresh dir on sys.path.
        tokens = [
            python,
            "-E",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--noconftest",
            "-c",
            str(config_path),
            "--rootdir",
            str(fresh_dir),
            f"--junitxml={junit_path}",
            "-q",
            str(fresh_dir / "tests" / "hidden"),
        ]
    else:
        node = "node"
        tokens = [
            node,
            "--experimental-strip-types",
            "--test",
            "--test-reporter=junit",
            f"--test-reporter-destination={junit_path}",
        ]
        if preload_path is not None:
            # Node treats a bare Windows path as a module specifier and fails to
            # load it; a file: URI works on every platform.
            tokens[1:1] = [f"--import={preload_path.resolve().as_uri()}"]
        # Node's glob expansion does not let `**` match zero directories on
        # every supported version, so pass both the flat and recursive forms.
        tokens.extend(("tests/hidden/*.test.ts", "tests/hidden/**/*.test.ts"))

    output = backend.run_argv(tokens, fresh_dir, timeout_s, env_extra=env)
    stdout, stderr = output.stdout, output.stderr
    timed_out = output.timed_out
    if timed_out:
        stderr += f"\nTIMEOUT after {timeout_s}s"

    counts = _parse_junit(junit_path)
    if counts is None:
        # A missing or malformed report means the tests did not run: that is a
        # failure, never a pass, whatever stdout claims.
        passed, failed, skipped = 0, 1, 0
    else:
        passed, failed, skipped = counts
    if timed_out:
        failed = max(failed, 1)
    total = passed + failed + skipped
    return TestOutcome(
        command=command,
        returncode=output.returncode,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )
