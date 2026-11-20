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


def restore_visible_tests(task: Task, workdir: Path) -> None:
    """Replace the agent's visible tests with the original ones from the task."""
    destination = workdir / task.visible_test_dir
    original = task.workspace_dir / task.visible_test_dir
    if destination.exists():
        shutil.rmtree(destination)
    copy_overlay(original, destination)


def overlay_hidden_tests(task: Task, workdir: Path) -> None:
    """Copy hidden tests into the agent's workspace."""
    copy_overlay(task.hidden_dir, workdir)
