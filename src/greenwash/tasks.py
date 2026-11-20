"""Task format loader and strict schema validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import yaml

from greenwash.models import Language, Task, TestCommands

_REQUIRED_KEYS = frozenset(
    {
        "id",
        "title",
        "language",
        "category",
        "difficulty",
        "time_budget_s",
        "test_commands",
        "sources",
    }
)
_OPTIONAL_KEYS = frozenset({"protected_files"})
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
_REFERENCE_IMPORT_RE = re.compile(
    r"(?:\b(?:from|import)\s+reference\b|reference\s*/|[\\/]reference[\\/]|['\"]reference['\"])"
)


class TaskError(ValueError):
    """Raised when a task directory does not satisfy the schema."""


def _string_list(value: object, field: str, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list of strings")
        return ()
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field}[{index}] must be a non-empty string")
        else:
            result.append(item)
    return tuple(result)


def validate_task(raw: object, root: Path) -> tuple[Task | None, list[str]]:
    """Validate a parsed ``task.yaml`` mapping against the greenwash schema.

    Returns the constructed task (or ``None`` when validation fails) together with
    every violation found, so callers can report all problems at once.
    """
    errors: list[str] = []
    if not isinstance(raw, dict):
        return None, ["task.yaml must contain a mapping"]

    mapping: dict[object, object] = cast(dict[object, object], raw)
    keys = {key for key in mapping if isinstance(key, str)}
    for missing in sorted(_REQUIRED_KEYS - keys):
        errors.append(f"missing required key: {missing}")
    for unknown in sorted(keys - _REQUIRED_KEYS - _OPTIONAL_KEYS):
        errors.append(f"unknown key: {unknown}")
    for non_string in sorted(str(key) for key in mapping if not isinstance(key, str)):
        errors.append(f"non-string key: {non_string}")

    def text(key: str) -> str:
        value = mapping.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")
            return ""
        return value

    task_id = text("id")
    title = text("title")
    category = text("category")
    difficulty = text("difficulty")
    language_raw = text("language")

    if task_id and not _ID_RE.fullmatch(task_id):
        errors.append("id must be lowercase kebab-case: [a-z0-9][a-z0-9-]*")
    if task_id and root.name and task_id != root.name:
        errors.append(f"id {task_id!r} does not match directory name {root.name!r}")

    language: Language | None = None
    try:
        language = Language(language_raw)
    except ValueError:
        errors.append(f"language must be one of {[str(item) for item in Language]}")

    budget = mapping.get("time_budget_s")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        errors.append("time_budget_s must be a positive integer")
        time_budget = 0
    else:
        time_budget = budget

    commands_raw = mapping.get("test_commands")
    commands: TestCommands | None = None
    if isinstance(commands_raw, dict):
        command_map = cast(dict[object, object], commands_raw)
        unexpected = sorted(str(key) for key in command_map if key not in {"visible", "hidden"})
        for key in unexpected:
            errors.append(f"test_commands has unknown key: {key}")
        visible = command_map.get("visible")
        hidden = command_map.get("hidden")
        if not isinstance(visible, str) or not visible.strip():
            errors.append("test_commands.visible must be a non-empty string")
        if not isinstance(hidden, str) or not hidden.strip():
            errors.append("test_commands.hidden must be a non-empty string")
        if (
            isinstance(visible, str)
            and isinstance(hidden, str)
            and visible.strip()
            and hidden.strip()
        ):
            commands = TestCommands(visible=visible, hidden=hidden)
    else:
        errors.append("test_commands must be a mapping with visible and hidden keys")

    sources = _string_list(mapping.get("sources"), "sources", errors)
    protected = _string_list(mapping.get("protected_files", []), "protected_files", errors)

    if errors or language is None or commands is None:
        return None, errors

    return (
        Task(
            root=root,
            id=task_id,
            title=title,
            language=language,
            category=category,
            difficulty=difficulty,
            time_budget_s=time_budget,
            test_commands=commands,
            sources=sources,
            protected_files=protected,
        ),
        errors,
    )


def load_task(root: Path) -> Task:
    """Load and validate one task directory. Raises ``TaskError`` on violations."""
    config_path = root / "task.yaml"
    if not root.is_dir():
        raise TaskError(f"task directory does not exist: {root}")
    if not config_path.is_file():
        raise TaskError(f"missing task.yaml: {config_path}")

    try:
        raw: object = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TaskError(f"invalid YAML in {config_path}: {exc}") from exc

    task, errors = validate_task(raw, root)
    errors.extend(_validate_layout(task))
    if errors:
        raise TaskError(f"invalid task {root.name}: " + "; ".join(errors))
    if task is None:  # pragma: no cover - errors always non-empty when task is None
        raise TaskError(f"invalid task {root.name}")
    return task


def _count_files(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    return sum(1 for path in directory.rglob("*") if path.is_file())


def _validate_layout(task: Task | None) -> list[str]:
    if task is None:
        return []
    errors: list[str] = []
    for directory in (
        task.workspace_dir,
        task.hidden_dir,
        task.reference_dir,
        task.traps_dir,
        task.mutants_dir,
    ):
        if not directory.is_dir():
            errors.append(f"missing directory: {directory.name}/")
    if task.spec_path.is_file():
        spec = task.spec_path.read_text(encoding="utf-8")
        if not spec.strip():
            errors.append("spec.md is empty")
        if _TODO_RE.search(spec):
            errors.append("spec.md contains a TODO marker")
    else:
        errors.append("missing spec.md")
    if (task.workspace_dir / task.visible_test_dir).is_dir() is False:
        errors.append("workspace must contain tests/visible/")
    if (task.hidden_dir / task.hidden_test_dir).is_dir() is False:
        errors.append("hidden must contain tests/hidden/")
    trap_count = _count_files(task.traps_dir)
    if trap_count < 2:
        errors.append(f"traps/ must contain at least 2 files (found {trap_count})")
    mutant_count = _count_files(task.mutants_dir)
    if mutant_count < 3:
        errors.append(f"mutants/ must contain at least 3 files (found {mutant_count})")
    return errors


def hidden_reference_imports(task: Task) -> list[str]:
    """Statically detect hidden tests that import or read the reference solution."""
    problems: list[str] = []
    hidden_dir = task.hidden_dir
    if not hidden_dir.is_dir():
        return problems
    for path in sorted(hidden_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in _REFERENCE_IMPORT_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            problems.append(f"{path.relative_to(task.root)}:{line}: references reference/ solution")
    return problems


def discover_tasks(root: Path, pattern: str = "*") -> tuple[Task, ...]:
    """Discover and validate tasks under ``root`` whose id matches ``pattern``."""
    if not root.is_dir():
        return ()
    tasks: list[Task] = []
    for config in sorted(root.glob("*/task.yaml")):
        if not fnmatch(config.parent.name, pattern):
            continue
        tasks.append(load_task(config.parent))
    return tuple(tasks)


def fnmatch(name: str, pattern: str) -> bool:
    """Small wrapper kept local to avoid leaking fnmatch's Any-typed cache."""
    import fnmatch as _fnmatch

    return bool(_fnmatch.fnmatchcase(name, pattern))
