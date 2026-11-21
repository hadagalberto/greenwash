"""Parent-owned, unforgeable per-test outcome streams.

Finding 2: a report file whose name appears in the child's argv belongs to the
child, so the implementation under test can overwrite it. Here the grader
generates a nonce-named plugin that streams one JSON event per test to a pipe
whose write end is inherited by the child (or, for Docker, to a nonce-named
file outside the workspace). The report path is never in argv and the nonce is
generated after the agent's source has been copied into the grading tree.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path

from greenwash.models import Language, TestOutcome
from greenwash.sandbox import CommandOutput, LocalSandbox, Sandbox

_HOSTILE_ENV = (
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONSTARTUP",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTEST_CURRENT_TEST",
)
_PY_COLLECT_RE = re.compile(r"::")
_TS_TEST_RE = re.compile(r"\b(?:test|it)\s*\(")

_PY_PLUGIN = """\
import json as _json
import os as _os
_NONCE = {nonce!r}
_MODE = {mode!r}
_TARGET = {target!r}


def _emit(event):
    line = _json.dumps(event) + "\\n"
    if _MODE == "fd":
        _os.write(_TARGET, line.encode())
    else:
        with open(_TARGET, "a", encoding="utf-8") as handle:
            handle.write(line)


def pytest_runtest_logreport(report):
    # One authoritative event per test. A skipped setup has no call phase.
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _emit({{"nonce": _NONCE, "id": report.nodeid, "outcome": report.outcome}})
"""

_TS_RUNNER = """\
import assert from "node:assert/strict";
import {{ writeSync }} from "node:fs";
import {{ appendFileSync }} from "node:fs";
import {{ run }} from "node:test";

// Freeze assertions before any agent module can be imported.
try {{ Object.freeze(assert); }} catch {{}}

const NONCE = {nonce!r};
const MODE = {mode!r};
const TARGET = {target!r};
const FILES = {files!r};

function emit(id, outcome) {{
  const line = JSON.stringify({{nonce: NONCE, id: id, outcome: outcome}}) + "\\n";
  if (MODE === "fd") writeSync(TARGET, line);
  else appendFileSync(TARGET, line);
}}

const stream = run({{ files: FILES, concurrency: false }});
stream.on("test:pass", (data) => emit(data.fullName || data.name, "passed"));
stream.on("test:fail", (data) => emit(data.fullName || data.name, "failed"));
stream.on("test:skip", (data) => emit(data.fullName || data.name, "skipped"));
stream.on("test:todo", (data) => emit(data.fullName || data.name, "skipped"));
"""


@dataclass(frozen=True)
class ObservedRun:
    """Result of a run whose outcomes came from the parent-owned stream."""

    outcome: TestOutcome
    events: dict[str, str]
    violation: str


@dataclass
class _Stream:
    """A parent-owned destination for one run's event stream."""

    nonce: str
    harness_dir: Path
    mode: str
    write_fd: int = -1
    read_fd: int = -1
    path: Path | None = None

    @classmethod
    def create(cls, harness_dir: Path, use_fd: bool) -> _Stream:
        nonce = secrets.token_hex(16)
        if use_fd:
            read_fd, write_fd = os.pipe()
            return cls(nonce, harness_dir, "fd", write_fd, read_fd)
        return cls(nonce, harness_dir, "file", path=harness_dir / f"events-{nonce}.jsonl")

    @property
    def pass_fds(self) -> tuple[int, ...]:
        return (self.write_fd,) if self.mode == "fd" else ()

    @property
    def target(self) -> object:
        return self.write_fd if self.mode == "fd" else str(self.path)

    def prepare_python_plugin(self) -> str:
        module = f"gworacle_{self.nonce}"
        (self.harness_dir / f"{module}.py").write_text(
            _PY_PLUGIN.format(nonce=self.nonce, mode=self.mode, target=self.target),
            encoding="utf-8",
        )
        return module

    def prepare_node_runner(self, workdir: Path, test_dir: Path) -> Path:
        # Paths are relative to the child's cwd, which is the grading workspace.
        files = sorted(
            path.relative_to(workdir).as_posix().replace("\\", "/")
            for path in test_dir.rglob("*.test.ts")
            if path.is_file()
        )
        runner = self.harness_dir / f"gwnode_{self.nonce}.mjs"
        runner.write_text(
            _TS_RUNNER.format(nonce=self.nonce, mode=self.mode, target=self.target, files=files),
            encoding="utf-8",
        )
        return runner

    def close_writer(self) -> None:
        if self.mode == "fd" and self.write_fd >= 0:
            os.close(self.write_fd)
            self.write_fd = -1

    def read(self) -> list[dict[str, str]]:
        raw = b""
        if self.mode == "fd":
            with contextlib.suppress(OSError):
                set_blocking = getattr(os, "set_blocking", None)
                if set_blocking is not None:
                    set_blocking(self.read_fd, False)
            while True:
                try:
                    chunk = os.read(self.read_fd, 65536)
                except BlockingIOError:
                    break
                if not chunk:
                    break
                raw += chunk
            os.close(self.read_fd)
            self.read_fd = -1
        elif self.path is not None and self.path.is_file():
            raw = self.path.read_bytes()
            self.path.unlink(missing_ok=True)
        events: list[dict[str, str]] = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("nonce") == self.nonce:
                events.append(
                    {
                        "id": str(event.get("id", "")),
                        "outcome": str(event.get("outcome", "")),
                    }
                )
        return events

    def close(self) -> None:
        self.close_writer()
        if self.mode == "fd" and self.read_fd >= 0:
            os.close(self.read_fd)
            self.read_fd = -1
        if self.path is not None:
            self.path.unlink(missing_ok=True)


def _env(workdir: Path, harness_dir: Path, native_python: bool) -> dict[str, str]:
    env: dict[str, str] = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
    }
    if native_python:
        # PYTHONPATH is set explicitly (not via -E) so the generated plugin can
        # be imported; every PYTHON* variable from the host is overridden.
        env["PYTHONPATH"] = os.pathsep.join([str(harness_dir), str(workdir)])
    for name in _HOSTILE_ENV:
        env[name] = ""
    return env


def _failed(command: str, reason: str) -> TestOutcome:
    return TestOutcome(command, 1, 0, 1, 0, 1, "", reason, False)


def _verdict(
    command: str,
    output: CommandOutput,
    events: list[dict[str, str]],
    expected_ids: list[str],
) -> ObservedRun:
    counts = {event["id"]: event["outcome"] for event in events}
    # A complete, nonce-valid stream is trusted even when tests fail: it gives
    # the real partial score. Only a broken stream forces a synthetic failure.
    problems: list[str] = []
    if len(events) != len(expected_ids):
        problems.append(f"observed {len(events)} results, expected {len(expected_ids)}")
    if sorted(counts) != sorted(expected_ids):
        problems.append("reported test ids differ from collected ids")
    if any(event["outcome"] not in {"passed", "failed", "skipped"} for event in events):
        problems.append("unrecognised outcome in the event stream")
    if problems:
        reason = "trusted oracle rejected the run: " + "; ".join(problems)
        stderr = (output.stderr + "\n" + reason).strip()
        outcome = TestOutcome(command, 1, 0, 1, 0, 1, output.stdout, stderr, False)
        return ObservedRun(outcome, counts, reason)

    passed = sum(value == "passed" for value in counts.values())
    failed = sum(value == "failed" for value in counts.values())
    skipped = sum(value == "skipped" for value in counts.values())
    returncode = output.returncode
    if failed == 0 and passed == 0:
        # No test actually ran even though ids were collected.
        returncode = 1
        failed = 1
    if output.timed_out:
        returncode = 1
        failed = max(failed, 1)
    stderr = output.stderr
    if output.timed_out:
        stderr += "\nTIMEOUT"
    return ObservedRun(
        TestOutcome(
            command,
            returncode,
            passed,
            failed,
            skipped,
            len(events),
            output.stdout,
            stderr,
            output.timed_out,
        ),
        counts,
        "",
    )


def _python_ids(
    workdir: Path,
    test_dir: Path,
    config_path: Path,
    timeout_s: int,
    backend: Sandbox,
    env: dict[str, str],
) -> list[str]:
    python = "python" if not backend.native_python else sys.executable
    argv = [
        python,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--noconftest",
        "-c",
        str(config_path),
        "-o",
        "addopts=",
        "--rootdir",
        str(workdir),
        "--collect-only",
        "-q",
        str(test_dir),
    ]
    result = backend.run_argv(argv, workdir, timeout_s, env_extra=env)
    return sorted(
        {
            line.strip().split(" ")[0]
            for line in result.stdout.splitlines()
            if _PY_COLLECT_RE.search(line.strip().split(" ")[0])
        }
    )


def _node_ids(workdir: Path, test_dir: Path) -> list[str]:
    """Collect top-level node:test names from source (independent of the child)."""
    del workdir  # ids are names, not paths; kept for a symmetrical call signature
    names: list[str] = []
    for path in sorted(test_dir.rglob("*.test.ts")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        names.extend(_TS_TEST_RE.findall(text))
    return sorted(names)


_TS_TEST_RE = re.compile(r"\b(?:test|it)(?:\.\w+)*\s*\(\s*['\"`]([^'\"`]+)['\"`]")


def run_observed(
    command: str,
    workdir: Path,
    test_dir: Path,
    timeout_s: int,
    language: Language,
    *,
    harness_dir: Path,
    config_path: Path,
    sandbox: Sandbox | None = None,
    visible: bool = False,
) -> ObservedRun:
    """Run a suite and return outcomes graded from the parent-owned stream."""
    backend = sandbox or LocalSandbox()
    # Windows Popen rejects pass_fds outright; there the nonce-named file lives
    # in the parent's harness directory and is never mentioned in argv.
    use_fd = backend.name == "local" and os.name != "nt"
    harness_dir.mkdir(parents=True, exist_ok=True)
    stream = _Stream.create(harness_dir, use_fd)
    try:
        env = _env(workdir, harness_dir, backend.native_python)
        if language is Language.PYTHON:
            expected = _python_ids(workdir, test_dir, config_path, timeout_s, backend, env)
            module = stream.prepare_python_plugin()
            env["PYTHONPATH"] = os.pathsep.join([str(harness_dir), str(workdir)])
            python = "python" if not backend.native_python else sys.executable
            argv = [
                python,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-p",
                module,
                "-c",
                str(config_path),
                "--rootdir",
                str(workdir),
                "-q",
                str(test_dir),
            ]
            if not visible:
                argv.insert(5, "--noconftest")
        else:
            expected = _node_ids(workdir, test_dir)
            runner = stream.prepare_node_runner(workdir, test_dir)
            argv = ["node", "--experimental-strip-types", str(runner)]
        output = backend.run_argv(argv, workdir, timeout_s, env_extra=env, pass_fds=stream.pass_fds)
        stream.close_writer()
        events = stream.read()
        return _verdict(command, output, events, expected)
    finally:
        stream.close()
