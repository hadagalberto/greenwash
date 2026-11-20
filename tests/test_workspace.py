"""Tests for isolated git-backed workspaces."""

from __future__ import annotations

from pathlib import Path

import pytest

from greenwash.models import Task
from greenwash.workspace import (
    Workspace,
    copy_overlay,
    git,
    overlay_hidden_tests,
    restore_visible_tests,
)


def test_workspace_is_git_initialised_with_baseline(crc_task: Task) -> None:
    with Workspace(crc_task) as workspace:
        assert workspace.path.is_dir()
        assert (workspace.path / "src" / "checksum.py").is_file()
        assert len(workspace.baseline_sha) == 40
        assert git(workspace.path, "status", "--porcelain").strip() == ""
        assert git(workspace.path, "log", "--oneline").count("baseline") == 1
    assert not workspace.path.exists()


def test_workspace_captures_staged_and_committed_changes(crc_task: Task) -> None:
    with Workspace(crc_task) as workspace:
        (workspace.path / "src" / "checksum.py").write_text("changed\n", encoding="utf-8")
        (workspace.path / "tests" / "visible" / "extra.test.py").write_text(
            "added\n", encoding="utf-8"
        )
        git(workspace.path, "add", "src/checksum.py")
        git(workspace.path, "commit", "-q", "-m", "agent commit")
        diff = workspace.capture_diff()
    assert "diff --git" in diff
    assert "changed" in diff
    assert "extra.test.py" in diff


def test_copy_overlay_requires_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        copy_overlay(tmp_path / "nope", tmp_path / "dest")


def test_copy_overlay_merges_directories(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("a", encoding="utf-8")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "b.txt").write_text("b", encoding="utf-8")
    copy_overlay(source, dest)
    assert (dest / "a.txt").read_text(encoding="utf-8") == "a"
    assert (dest / "b.txt").read_text(encoding="utf-8") == "b"


def test_restore_and_overlay_tests(crc_task: Task, tmp_path: Path) -> None:
    with Workspace(crc_task) as workspace:
        visible = workspace.path / "tests" / "visible" / "test_crc32.py"
        original = visible.read_text(encoding="utf-8")
        visible.write_text("tampered", encoding="utf-8")
        restore_visible_tests(crc_task, workspace.path)
        assert visible.read_text(encoding="utf-8") == original

        overlay_hidden_tests(crc_task, workspace.path)
        hidden = workspace.path / "tests" / "hidden" / "test_crc32_hidden.py"
        assert hidden.is_file()
