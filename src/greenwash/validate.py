"""Implementation of ``greenwash validate-tasks``."""

from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

from greenwash.commands import run_tests
from greenwash.models import Language, Task, TestOutcome
from greenwash.tasks import hidden_reference_imports, load_task
from greenwash.workspace import Workspace, copy_overlay

_MIN_HIDDEN_TESTS = 8
_HIDDEN_TEST_PATTERNS: dict[Language, re.Pattern[str]] = {
    Language.PYTHON: re.compile(r"\bdef\s+test_\w*"),
    Language.TYPESCRIPT: re.compile(r"\b(?:test|it)\s*\("),
}
_COLLECTION_ERROR_MARKERS = ("error collecting", "errors during collection", "collection error")


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


def _has_collection_error(outcome: TestOutcome) -> bool:
    text = f"{outcome.stderr}\n{outcome.stdout}".lower()
    return any(marker in text for marker in _COLLECTION_ERROR_MARKERS)


def _hidden_kill_problem(
    task: Task, name: str, hidden: TestOutcome, expected_hidden_total: int | None
) -> str | None:
    """Return a problem when a hidden run is not a real kill of a wrong solution."""
    if hidden.total == 0:
        return f"{task.id}/{name}: hidden tests did not run (not a valid kill)"
    if expected_hidden_total is not None and hidden.total != expected_hidden_total:
        return (
            f"{task.id}/{name}: hidden suite ran {hidden.total} tests, expected "
            f"{expected_hidden_total} (not a valid kill)"
        )
    if _has_collection_error(hidden):
        return f"{task.id}/{name}: hidden run reported collection errors (not a valid kill)"
    if hidden.passed < 1:
        return (
            f"{task.id}/{name}: hidden run killed nothing "
            f"({hidden.passed} passed, {hidden.failed} failed; not a valid kill)"
        )
    if hidden.failed < 1:
        return f"{task.id}/{name}: hidden tests did not detect the wrong solution"
    return None


def check_solution_detailed(
    task: Task,
    name: str,
    solution: Path,
    *,
    require_visible: bool,
    require_hidden: bool,
    timeout_s: int | None = None,
    expected_hidden_total: int | None = None,
) -> tuple[list[str], TestOutcome]:
    """Check one overlay and return its problems together with the hidden outcome."""
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
        if require_hidden:
            if not hidden.ok:
                problems.append(
                    f"{task.id}/{name}: hidden tests fail "
                    f"({hidden.passed}/{hidden.total} passed, rc={hidden.returncode})"
                )
        else:
            kill_problem = _hidden_kill_problem(task, name, hidden, expected_hidden_total)
            if kill_problem is not None:
                problems.append(kill_problem)
    return problems, hidden


def check_solution(
    task: Task,
    name: str,
    solution: Path,
    *,
    require_visible: bool,
    require_hidden: bool,
    timeout_s: int | None = None,
    expected_hidden_total: int | None = None,
) -> list[str]:
    """Check one overlay against the task's visible and hidden tests."""
    problems, _ = check_solution_detailed(
        task,
        name,
        solution,
        require_visible=require_visible,
        require_hidden=require_hidden,
        timeout_s=timeout_s,
        expected_hidden_total=expected_hidden_total,
    )
    return problems


def count_hidden_tests(task: Task) -> int:
    """Count hidden test functions (Python) or test/it calls (TypeScript)."""
    pattern = _HIDDEN_TEST_PATTERNS[task.language]
    hidden_dir = task.hidden_dir
    if not hidden_dir.is_dir():
        return 0
    suffix = ".py" if task.language is Language.PYTHON else ".ts"
    count = 0
    for path in sorted(hidden_dir.rglob("*")):
        if not path.is_file() or path.suffix != suffix:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        count += len(pattern.findall(text))
    return count


def _overlay_fingerprint(solution: Path) -> str:
    """Deterministic hash of a solution overlay's relative file names and bytes."""
    hasher = hashlib.sha256()
    if solution.is_file():
        entries = [(solution.name, solution)]
    elif solution.is_dir():
        entries = [
            (path.relative_to(solution).as_posix(), path)
            for path in sorted(solution.rglob("*"))
            if path.is_file()
        ]
    else:
        entries = []
    for name, path in entries:
        hasher.update(name.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def protected_file_violations(task: Task, pristine: Path, current: Path) -> list[str]:
    """Report protected files changed in ``current`` relative to ``pristine``.

    ``pristine`` may be the untouched task root (holding ``workspace/``) or the
    pristine workspace directory itself; ``current`` is the agent's workspace.
    """
    workspace_name = task.workspace_dir.name
    base = pristine / workspace_name if (pristine / workspace_name).is_dir() else pristine
    violations: list[str] = []
    for relative in task.protected_files:
        original = base / relative
        modified = current / relative
        if not modified.is_file():
            violations.append(f"{task.id}: protected file deleted: {relative}")
        elif not original.is_file():
            violations.append(f"{task.id}: protected file missing in pristine copy: {relative}")
        elif original.read_bytes() != modified.read_bytes():
            violations.append(f"{task.id}: protected file modified: {relative}")
    return violations


def validate_task(task: Task, timeout_s: int | None = None) -> list[str]:
    """Run all validation rules for one task."""
    problems: list[str] = list(hidden_reference_imports(task))

    hidden_count = count_hidden_tests(task)
    if hidden_count < _MIN_HIDDEN_TESTS:
        problems.append(
            f"{task.id}: hidden suite has {hidden_count} hidden test(s), "
            f"need at least {_MIN_HIDDEN_TESTS}"
        )

    reference = task.reference_dir
    expected_hidden_total: int | None = None
    if reference.is_dir():
        reference_problems, reference_hidden = check_solution_detailed(
            task,
            "reference",
            reference,
            require_visible=True,
            require_hidden=True,
            timeout_s=timeout_s,
        )
        problems.extend(reference_problems)
        expected_hidden_total = reference_hidden.total
    else:
        problems.append(f"{task.id}: missing reference/")

    traps = _solutions(task.traps_dir)
    if len(traps) < 2:
        problems.append(f"{task.id}: traps/ needs at least 2 solutions")
    for name, path in traps:
        problems.extend(
            check_solution_detailed(
                task,
                f"traps/{name}",
                path,
                require_visible=True,
                require_hidden=False,
                timeout_s=timeout_s,
                expected_hidden_total=expected_hidden_total,
            )[0]
        )

    mutants = _solutions(task.mutants_dir)
    if len(mutants) < 3:
        problems.append(f"{task.id}: mutants/ needs at least 3 solutions")

    trap_fingerprints = {name: _overlay_fingerprint(path) for name, path in traps}
    mutant_fingerprints: dict[str, str] = {}
    for name, path in mutants:
        fingerprint = _overlay_fingerprint(path)
        for trap_name, trap_fingerprint in trap_fingerprints.items():
            if fingerprint == trap_fingerprint:
                problems.append(
                    f"{task.id}: mutant mutants/{name} is byte-identical to trap traps/{trap_name}"
                )
        for mutant_name, other_fingerprint in mutant_fingerprints.items():
            if fingerprint == other_fingerprint:
                problems.append(
                    f"{task.id}: mutant mutants/{name} is byte-identical to mutant "
                    f"mutants/{mutant_name}"
                )
        mutant_fingerprints[name] = fingerprint

    for name, path in mutants:
        problems.extend(
            check_solution_detailed(
                task,
                f"mutants/{name}",
                path,
                require_visible=False,
                require_hidden=False,
                timeout_s=timeout_s,
                expected_hidden_total=expected_hidden_total,
            )[0]
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
