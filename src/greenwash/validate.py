"""Implementation of ``greenwash validate-tasks``."""

from __future__ import annotations

import shutil
from pathlib import Path

from greenwash.commands import run_tests
from greenwash.models import Task
from greenwash.tasks import hidden_reference_imports, load_task
from greenwash.workspace import Workspace, copy_overlay


def _solutions(root: Path) -> list[tuple[str, Path]]:
    if not root.is_dir():
        return []
    return [
        (entry.name, entry) for entry in sorted(root.iterdir()) if entry.is_dir() or entry.is_file()
    ]


def _apply_solution(solution: Path, workdir: Path) -> None:
    if solution.is_dir():
        copy_overlay(solution, workdir)
    else:
        target = workdir / solution.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(solution, target)


def check_solution(
    task: Task,
    name: str,
    solution: Path,
    *,
    require_visible: bool,
    require_hidden: bool,
    timeout_s: int | None = None,
) -> list[str]:
    """Check one overlay against the task's visible and hidden tests."""
    budget = task.time_budget_s if timeout_s is None else timeout_s
    problems: list[str] = []
    with Workspace(task) as workspace:
        _apply_solution(solution, workspace.path)
        visible = run_tests(task.test_commands.visible, workspace.path, budget, task.language)
        copy_overlay(task.hidden_dir, workspace.path)
        hidden = run_tests(task.test_commands.hidden, workspace.path, budget, task.language)

        if require_visible and not visible.ok:
            problems.append(
                f"{task.id}/{name}: visible tests fail "
                f"({visible.passed}/{visible.total} passed, rc={visible.returncode})"
            )
        if require_hidden and not hidden.ok:
            problems.append(
                f"{task.id}/{name}: hidden tests fail "
                f"({hidden.passed}/{hidden.total} passed, rc={hidden.returncode})"
            )
        if not require_hidden and hidden.ok:
            problems.append(f"{task.id}/{name}: hidden tests did not detect the wrong solution")
    return problems


def validate_task(task: Task, timeout_s: int | None = None) -> list[str]:
    """Run all validation rules for one task."""
    problems: list[str] = list(hidden_reference_imports(task))

    reference = task.reference_dir
    if reference.is_dir():
        problems.extend(
            check_solution(
                task,
                "reference",
                reference,
                require_visible=True,
                require_hidden=True,
                timeout_s=timeout_s,
            )
        )
    else:
        problems.append(f"{task.id}: missing reference/")

    traps = _solutions(task.traps_dir)
    if len(traps) < 2:
        problems.append(f"{task.id}: traps/ needs at least 2 solutions")
    for name, path in traps:
        problems.extend(
            check_solution(
                task,
                f"traps/{name}",
                path,
                require_visible=True,
                require_hidden=False,
                timeout_s=timeout_s,
            )
        )

    mutants = _solutions(task.mutants_dir)
    if len(mutants) < 3:
        problems.append(f"{task.id}: mutants/ needs at least 3 solutions")
    for name, path in mutants:
        problems.extend(
            check_solution(
                task,
                f"mutants/{name}",
                path,
                require_visible=False,
                require_hidden=False,
                timeout_s=timeout_s,
            )
        )
    return problems


def validate_all(task_roots: list[Path], timeout_s: int | None = None) -> tuple[bool, list[str]]:
    """Validate every task root. Returns (success, all violations)."""
    problems: list[str] = []
    for root in task_roots:
        try:
            task = load_task(root)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        problems.extend(validate_task(task, timeout_s=timeout_s))
    return not problems, problems
