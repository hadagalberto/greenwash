"""Tests for task loading and schema validation."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from greenwash.models import Language, Task
from greenwash.tasks import (
    TaskError,
    discover_tasks,
    hidden_reference_imports,
    load_task,
    validate_task,
)

VALID_RAW: dict[str, object] = {
    "id": "demo",
    "title": "Demo",
    "language": "python",
    "category": "parsing",
    "difficulty": "easy",
    "time_budget_s": 30,
    "test_commands": {"visible": "pytest", "hidden": "pytest hidden"},
    "sources": ["https://example.org/spec"],
}


def test_load_fixture_tasks(crc_task: Task, base64_task: Task, semver_task: Task) -> None:
    assert crc_task.language is Language.PYTHON
    assert base64_task.language is Language.TYPESCRIPT
    assert semver_task.language is Language.TYPESCRIPT
    assert crc_task.time_budget_s == 120
    assert crc_task.test_commands.visible.startswith("python -m pytest")
    assert base64_task.sources == ("https://www.rfc-editor.org/rfc/rfc4648.txt",)
    assert semver_task.visible_test_dir == Path("tests/visible")


def test_validate_task_accepts_valid_mapping() -> None:
    task, errors = validate_task(VALID_RAW, Path("demo"))
    assert errors == []
    assert task is not None
    assert task.id == "demo"
    assert task.protected_files == ()


@pytest.mark.parametrize("missing", ["id", "title", "language", "time_budget_s", "sources"])
def test_validate_task_reports_missing_keys(missing: str) -> None:
    raw = dict(VALID_RAW)
    del raw[missing]
    task, errors = validate_task(raw, Path("demo"))
    assert task is None
    assert f"missing required key: {missing}" in errors


def test_validate_task_reports_unknown_and_non_string_keys() -> None:
    raw = dict(VALID_RAW)
    raw["surprise"] = 1
    raw[3] = "bad"  # type: ignore[index]
    task, errors = validate_task(raw, Path("demo"))
    assert task is None
    assert "unknown key: surprise" in errors
    assert "non-string key: 3" in errors


def test_validate_task_reports_bad_types_and_mismatched_id() -> None:
    raw = dict(VALID_RAW)
    raw.update({"id": "Other", "time_budget_s": -1, "language": "rust", "sources": [1, ""]})
    task, errors = validate_task(raw, Path("demo"))
    assert task is None
    assert any("kebab-case" in error for error in errors)
    assert any("directory name" in error for error in errors)
    assert "time_budget_s must be a positive integer" in errors
    assert any("language must be one of" in error for error in errors)
    assert "sources[0] must be a non-empty string" in errors
    assert "sources[1] must be a non-empty string" in errors


def test_validate_task_reports_bad_commands() -> None:
    raw = dict(VALID_RAW)
    raw["test_commands"] = {"visible": "", "extra": "x"}
    task, errors = validate_task(raw, Path("demo"))
    assert task is None
    assert "test_commands has unknown key: extra" in errors
    assert "test_commands.visible must be a non-empty string" in errors
    assert "test_commands.hidden must be a non-empty string" in errors

    raw["test_commands"] = ["pytest"]
    _, errors = validate_task(raw, Path("demo"))
    assert "test_commands must be a mapping with visible and hidden keys" in errors

    raw = dict(VALID_RAW)
    raw["sources"] = "not a list"
    _, errors = validate_task(raw, Path("demo"))
    assert "sources must be a list of strings" in errors


def test_validate_task_rejects_non_mapping() -> None:
    task, errors = validate_task(["nope"], Path("demo"))
    assert task is None
    assert errors == ["task.yaml must contain a mapping"]


def test_load_task_rejects_missing_config(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(TaskError, match="missing task.yaml"):
        load_task(empty)


def test_load_task_rejects_bad_yaml(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "task.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    with pytest.raises(TaskError, match="invalid YAML"):
        load_task(root)


def test_load_task_rejects_layout_problems(tmp_path: Path, tasks_dir: Path) -> None:
    root = tmp_path / "crc32-check"
    shutil.copytree(tasks_dir / "crc32-check", root)
    (root / "spec.md").write_text("Do a TODO here", encoding="utf-8")
    shutil.rmtree(root / "mutants")
    (root / "task.yaml").write_text(
        yaml.safe_dump({**VALID_RAW, "id": "crc32-check"}), encoding="utf-8"
    )
    with pytest.raises(TaskError) as exc:
        load_task(root)
    message = str(exc.value)
    assert "spec.md contains a TODO marker" in message
    assert "missing directory: mutants/" in message


def test_hidden_reference_imports_detects_violation(crc_task: Task, tmp_path: Path) -> None:
    assert hidden_reference_imports(crc_task) == []
    hidden = tmp_path / "hidden" / "tests" / "hidden"
    hidden.mkdir(parents=True)
    (hidden / "test_bad.py").write_text("from reference import solution\n", encoding="utf-8")
    task = Task(
        root=tmp_path,
        id=crc_task.id,
        title=crc_task.title,
        language=crc_task.language,
        category=crc_task.category,
        difficulty=crc_task.difficulty,
        time_budget_s=crc_task.time_budget_s,
        test_commands=crc_task.test_commands,
        sources=crc_task.sources,
        protected_files=crc_task.protected_files,
    )
    problems = hidden_reference_imports(task)
    assert len(problems) == 1
    assert "test_bad.py:1" in problems[0]


def test_discover_tasks_filters_by_glob(tasks_dir: Path) -> None:
    assert len(discover_tasks(tasks_dir)) == 3
    assert [task.id for task in discover_tasks(tasks_dir, "base*")] == ["base64url"]
    assert discover_tasks(tasks_dir / "missing") == ()
