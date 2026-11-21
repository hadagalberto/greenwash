"""Isolated per-attempt workspaces backed by a local git repository.

The agent's own ``.git`` is never trusted for grading.  The diff is computed
in Python against a pristine snapshot taken before the agent runs, and hidden
tests are graded in a fresh harness-owned directory.  That keeps hostile git
config (fsmonitor, textconv, replace refs), ignore files and conftest/plugins
out of the measurement.
"""

from __future__ import annotations

import contextlib
import difflib
import logging
import os
import shutil
import stat
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from types import TracebackType

from greenwash.implscan import format_findings, scan_source
from greenwash.models import Task

_GIT_OPTIONS = (
    "-c",
    "core.autocrlf=false",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "user.name=greenwash",
    "-c",
    "user.email=greenwash@invalid.local",
)

# Test configuration must never come from the agent's tree.  These names are
# also recognised by the tamper analyser as ``test_config_changed``.
_TEST_CONFIG_NAMES = frozenset(
    {
        "conftest.py",
        "pytest.ini",
        "pyproject.toml",
        "setup.cfg",
        "tox.ini",
        "sitecustomize.py",
        "usercustomize.py",
        "package.json",
    }
)


def git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run a git command inside ``cwd`` and return stdout.

    Retained for workspace setup and for the test-suite's own assertions.  The
    grading path does not call this function on the agent's repository.
    """
    result = subprocess.run(
        ["git", "-C", str(cwd), *_GIT_OPTIONS, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
    return result.stdout


def _reparse(path: Path) -> bool:
    """True for a POSIX symlink or a Windows junction/reparse point."""
    if not os.path.lexists(path):
        return False
    if path.is_symlink():
        return True
    flags = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(flags & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _walk(root: Path) -> Iterator[Path]:
    """Yield every entry under ``root`` (excluding its own ``.git``) using lstat."""
    if not root.is_dir():
        return
    for entry in sorted(root.iterdir()):
        if entry.name == ".git":
            continue
        yield entry
        if entry.is_dir() and not _reparse(entry):
            yield from _walk(entry)


def find_escape_symlinks(workdir: Path) -> list[str]:
    """Return workspace-relative paths of links resolving outside ``workdir``.

    Following such a link while restoring or overlaying tests would let an
    agent delete or write files outside its sandbox (a POSIX symlink or a
    Windows junction both qualify).
    """
    root = workdir.resolve()
    escapes: list[str] = []
    for path in _walk(workdir):
        if not _reparse(path):
            continue
        try:
            target = path.resolve()
        except (OSError, RuntimeError):
            escapes.append(path.relative_to(workdir).as_posix())
            continue
        if not target.is_relative_to(root):
            escapes.append(path.relative_to(workdir).as_posix())
    return escapes


def copy_overlay(source: Path, destination: Path) -> None:
    """Copy ``source`` recursively over ``destination`` (files are overwritten)."""
    if not source.is_dir():
        raise FileNotFoundError(f"overlay directory does not exist: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True)


def _rel_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in _walk(root)
        if not path.is_dir() or _reparse(path)
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return ""


def _unified_diff(pristine: Path, current: Path) -> str:
    """Build a git-style diff without invoking git in the agent's workspace."""
    old = {rel: _read_text(pristine / rel) for rel in _rel_files(pristine)}
    new = {rel: _read_text(current / rel) for rel in _rel_files(current)}
    chunks: list[str] = []
    for rel in sorted(set(old) | set(new)):
        before = old.get(rel)
        after = new.get(rel)
        if before == after:
            continue
        header = f"diff --git a/{rel} b/{rel}"
        if before is None:
            chunks.append(f"{header}\nnew file mode 100644")
        elif after is None:
            chunks.append(f"{header}\ndeleted file mode 100644")
        else:
            chunks.append(header)
        old_lines = before.splitlines(keepends=True) if before is not None else []
        new_lines = after.splitlines(keepends=True) if after is not None else []
        chunks.append(
            "".join(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="\n",
                    n=3,
                )
            ).rstrip("\n")
        )
    return "\n".join(chunks) + ("\n" if chunks else "")


class Workspace:
    """A temporary git-initialised copy of a task workspace."""

    def __init__(self, task: Task):
        self.task = task
        self.path = Path(tempfile.mkdtemp(prefix="greenwash-"))
        self.pristine = Path(tempfile.mkdtemp(prefix="greenwash-pristine-"))
        self.baseline_sha = ""
        copy_overlay(task.workspace_dir, self.path)
        copy_overlay(task.workspace_dir, self.pristine)
        git(self.path, "init", "-q")
        # Prompt files are created inside the workspace so docker mounts expose
        # them; they are transient and must never appear in the graded diff.
        info_dir = self.path / ".git" / "info"
        info_dir.mkdir(parents=True, exist_ok=True)
        (info_dir / "exclude").write_text(".greenwash-prompt-*.md\n", encoding="utf-8")
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", "baseline")
        self.baseline_sha = git(self.path, "rev-parse", "HEAD").strip()

    def capture_diff(self, unified: int = 3) -> str:
        """Return the diff from the pristine snapshot to the current workspace.

        Computed with :mod:`difflib` so the agent's git configuration, replace
        refs and ignore files cannot hide changes or execute host commands.
        ``unified`` is accepted for API compatibility; the analyser uses whole
        hunks and is insensitive to context size.
        """
        return _unified_diff(self.pristine, self.path)

    def symlink_violations(self) -> list[str]:
        return find_escape_symlinks(self.path)

    def close(self) -> None:
        def make_writable(function: Callable[[str], object], path: str, _: object) -> None:
            with contextlib.suppress(OSError):
                os.chmod(path, stat.S_IWRITE)
            function(path)

        for directory in (self.path, self.pristine):
            # A detached child (finding 5) may briefly hold a file open after
            # the run. Retry, then log and move on: cleanup must never turn a
            # completed attempt into a crash.
            for attempt in range(4):
                try:
                    shutil.rmtree(directory, onerror=make_writable)
                    break
                except OSError as exc:
                    if attempt == 3:
                        logging.getLogger(__name__).warning(
                            "could not remove workspace %s: %s", directory, exc
                        )
                    else:
                        time.sleep(0.1 * (attempt + 1))

    def __enter__(self) -> Workspace:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _remove_path(path: Path) -> None:
    """Remove a file or directory, never following a link into another tree."""
    if not os.path.lexists(path):
        return
    if _reparse(path) or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def restore_visible_tests(task: Task, workdir: Path) -> None:
    """Replace the agent's visible tests with the original ones from the task."""
    destination = workdir / task.visible_test_dir
    original = task.workspace_dir / task.visible_test_dir
    _remove_path(destination)
    copy_overlay(original, destination)


def overlay_hidden_tests(task: Task, workdir: Path) -> None:
    """Copy hidden tests into the agent's workspace (legacy visible-test path).

    Grading itself uses :func:`build_grading_dir`; this helper remains for the
    original-visible run and for the test-suite's compatibility checks.
    """
    _remove_path(workdir / task.hidden_test_dir)
    copy_overlay(task.hidden_dir, workdir)


def build_grading_dir(task: Task, agent_path: Path, destination: Path) -> list[str]:
    """Populate a fresh harness-owned directory for hidden grading.

    Only pristine non-test support files plus the task's declared
    ``implementation_files`` (taken from the agent's tree) are copied.  Agent
    conftests, pytest configuration, sitecustomize hooks and plugins therefore
    never influence the hidden run.  Returns the relative paths of any
    implementation files that import the test framework (oracle interference).
    """
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    # Start from a clean copy of the task's own workspace, dropping all test
    # files and test configuration.  This keeps non-test support modules.
    for path in _walk(task.workspace_dir):
        rel = path.relative_to(task.workspace_dir)
        if rel.parts[0] in {"tests", "test"} or path.name in _TEST_CONFIG_NAMES:
            continue
        target = destination / rel
        if path.is_dir() and not _reparse(path):
            target.mkdir(parents=True, exist_ok=True)
        elif not _reparse(path):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    implementation = list(task.implementation_files)
    if not implementation:
        implementation = [
            path.relative_to(task.workspace_dir).as_posix()
            for path in _walk(task.workspace_dir / "src")
            if path.is_file() and not _reparse(path)
        ]

    interference: list[str] = []
    for rel_path in implementation:
        source = agent_path / rel_path
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not source.is_file() or _reparse(source):
            # A deleted implementation must make hidden tests fail, so leave
            # the file absent rather than silently restoring the reference.
            if target.exists():
                target.unlink()
            continue
        shutil.copy2(source, target)
        language = "typescript" if source.suffix in {".ts", ".tsx", ".mts", ".cts"} else "python"
        findings = scan_source(_read_text(source), language)
        if findings:
            interference.append(format_findings(rel_path, findings))

    copy_overlay(task.workspace_dir / task.visible_test_dir, destination / task.visible_test_dir)
    copy_overlay(task.hidden_dir / task.hidden_test_dir, destination / task.hidden_test_dir)
    return interference
