"""Tests for the validate-tasks command implementation."""

from __future__ import annotations

import shutil
from pathlib import Path

from greenwash.models import Task
from greenwash.tasks import load_task
from greenwash.validate import check_solution, validate_all, validate_task


def test_all_fixture_tasks_are_valid(tasks_dir: Path) -> None:
    ok, problems = validate_all(
        [tasks_dir / name for name in sorted(path.name for path in tasks_dir.iterdir())]
    )
    assert ok is True
    assert problems == []


def test_reference_traps_and_mutants_are_checked(crc_task: Task) -> None:
    problems = validate_task(crc_task)
    assert problems == []


def test_check_solution_detects_weak_hidden_suite(crc_task: Task, tmp_path: Path) -> None:
    # A wrong-but-plausible stub fails visible tests, so it cannot be a reference.
    overlay = tmp_path / "stub" / "src"
    overlay.mkdir(parents=True)
    (overlay / "checksum.py").write_text("def crc32(data):\n    return 0\n", encoding="utf-8")
    problems = check_solution(
        crc_task,
        "stub",
        overlay.parent,
        require_visible=True,
        require_hidden=True,
    )
    assert any("visible tests fail" in problem for problem in problems)


def test_validate_all_reports_broken_reference(tasks_dir: Path, tmp_path: Path) -> None:
    root = tmp_path / "crc32-check"
    shutil.copytree(tasks_dir / "crc32-check", root)
    (root / "reference" / "src" / "checksum.py").write_text(
        "def crc32(data):\n    return 0\n", encoding="utf-8"
    )
    ok, problems = validate_all([root])
    assert ok is False
    assert any("reference" in problem and "hidden tests fail" in problem for problem in problems)


def test_validate_all_reports_invalid_task(tmp_path: Path) -> None:
    ok, problems = validate_all([tmp_path / "not-a-task"])
    assert ok is False
    assert any(
        "missing task.yaml" in problem or "does not exist" in problem for problem in problems
    )


def test_validate_detects_hidden_reference_import(tasks_dir: Path, tmp_path: Path) -> None:
    root = tmp_path / "crc32-check"
    shutil.copytree(tasks_dir / "crc32-check", root)
    hidden = root / "hidden" / "tests" / "hidden" / "test_leak.py"
    hidden.write_text("from reference.src.checksum import crc32\n", encoding="utf-8")
    task = load_task(root)
    problems = validate_task(task)
    assert any("references reference/ solution" in problem for problem in problems)
