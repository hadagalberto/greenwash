"""Isolated per-attempt workspaces backed by a local git repository."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import TracebackType

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


def git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run a git command inside ``cwd`` and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(cwd), *_GIT_OPTIONS, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
    return result.stdout


def copy_overlay(source: Path, destination: Path) -> None:
    """Copy ``source`` recursively over ``destination`` (files are overwritten)."""
    if not source.is_dir():
        raise FileNotFoundError(f"overlay directory does not exist: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


class Workspace:
    """A temporary git-initialised copy of a task workspace."""

    def __init__(self, task: Task):
        self.path = Path(tempfile.mkdtemp(prefix="greenwash-"))
        self.baseline_sha = ""
        copy_overlay(task.workspace_dir, self.path)
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
        """Return the full diff from the baseline to the current workspace state.

        Everything is staged first so that agent-created files and agent-made
        commits are both included.
        """
        git(self.path, "add", "-A")
        return git(
            self.path,
            "diff",
            "--cached",
            "--no-color",
            "--no-ext-diff",
            f"--unified={unified}",
            self.baseline_sha,
        )

    def close(self) -> None:
        def make_writable(function: Callable[[str], object], path: str, _: object) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)

        shutil.rmtree(self.path, onerror=make_writable)

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
    """Remove a file, directory or symlink left behind by an agent."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def restore_visible_tests(task: Task, workdir: Path) -> None:
    """Replace the agent's visible tests with the original ones from the task."""
    destination = workdir / task.visible_test_dir
    original = task.workspace_dir / task.visible_test_dir
    _remove_path(destination)
    copy_overlay(original, destination)


def overlay_hidden_tests(task: Task, workdir: Path) -> None:
    """Copy hidden tests into the agent's workspace.

    The agent may have created files under ``tests/hidden/`` itself (the
    workspace starts without that directory). Copying with ``dirs_exist_ok``
    would leave those files in place, where pytest could load a malicious
    ``conftest.py`` and change the hidden tests' behaviour. Remove the whole
    directory first so the hidden suite is exactly the task's own copy.
    """
    _remove_path(workdir / task.hidden_test_dir)
    copy_overlay(task.hidden_dir, workdir)
