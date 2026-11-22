"""Milestone 9 validator-hardening regression tests (TDD, hand-derived values)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import greenwash.models as models
from greenwash import validate as validate_module
from greenwash.models import Language, Task
from greenwash.tasks import validate_task as validate_task_schema

_VALID_RAW: dict[str, object] = {
    "id": "demo",
    "title": "Demo",
    "language": "python",
    "category": "parsing",
    "difficulty": "easy",
    "time_budget_s": 30,
    "test_commands": {"visible": "pytest", "hidden": "pytest hidden"},
    "sources": ["https://example.org/spec"],
}


def _task(
    root: Path,
    *,
    language: Language = Language.PYTHON,
    protected: tuple[str, ...] = (),
    implementation: tuple[str, ...] = (),
) -> Task:
    return Task(
        root=root,
        id=root.name or "demo",
        title="Demo",
        language=language,
        category="parsing",
        difficulty="easy",
        time_budget_s=30,
        test_commands=models.TestCommands(
            visible="python -m pytest -q tests/visible", hidden="python -m pytest -q tests/hidden"
        ),
        sources=(),
        protected_files=protected,
        implementation_files=implementation,
    )


def _outcome(
    *,
    passed: int,
    failed: int,
    total: int,
    returncode: int = 1,
    stderr: str = "",
) -> models.TestOutcome:
    return models.TestOutcome(
        command="python -m pytest -q tests/hidden",
        returncode=returncode,
        passed=passed,
        failed=failed,
        skipped=0,
        total=total,
        stdout="",
        stderr=stderr,
        timed_out=False,
    )


def _patch_outcomes(monkeypatch: pytest.MonkeyPatch, outcomes: list[models.TestOutcome]) -> None:
    """Feed hand-written outcomes to the validator's real oracle seam.

    Round-3 finding 1 replaced the text-parsing ``run_tests`` call with
    ``_run_oracle`` (the same parent-owned oracle used by grading). The test
    double follows that seam so the kill/reference rules are still exercised
    without weakening any assertion.
    """
    sequence = iter(outcomes)

    def fake_oracle(
        command: str,
        workdir: Path,
        test_dir: Path,
        timeout_s: int,
        language: Language,
        *,
        visible: bool,
    ) -> models.TestOutcome:
        return next(sequence)

    monkeypatch.setattr(validate_module, "_run_oracle", fake_oracle)


def _prepared_task(tmp_path: Path, name: str) -> Task:
    task = _task(tmp_path / name)
    source = task.workspace_dir / "src" / "x.py"
    source.parent.mkdir(parents=True)
    source.write_text("x = 0\n", encoding="utf-8")
    task.hidden_dir.mkdir(parents=True)
    return task


def _stub_check_solution(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(
        task: Task,
        name: str,
        solution: Path,
        *,
        require_visible: bool,
        require_hidden: bool,
        timeout_s: int | None = None,
        expected_hidden_total: int | None = None,
    ) -> tuple[list[str], models.TestOutcome]:
        return [], _outcome(passed=10, failed=0, total=10, returncode=0)

    monkeypatch.setattr(validate_module, "check_solution_detailed", fake, raising=False)

    def fake_simple(
        task: Task,
        name: str,
        solution: Path,
        *,
        require_visible: bool,
        require_hidden: bool,
        timeout_s: int | None = None,
        expected_hidden_total: int | None = None,
    ) -> list[str]:
        return []

    monkeypatch.setattr(validate_module, "check_solution", fake_simple, raising=False)


def _static_task(root: Path, *, language: Language = Language.PYTHON) -> Task:
    task = _task(root, language=language)
    for directory in (
        task.workspace_dir / "tests" / "visible",
        task.hidden_dir / "tests" / "hidden",
        task.reference_dir / "src",
        task.traps_dir,
        task.mutants_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    (root / "spec.md").write_text("A valid, complete specification.", encoding="utf-8")
    return task


def _write_overlay(base: Path, name: str, *, source: str, filename: str = "x.py") -> Path:
    overlay = base / name
    target = overlay / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return overlay


# ---------------------------------------------------------------------------
# Finding 13: hidden-run must be a real kill, not a crash
# ---------------------------------------------------------------------------


def test_hidden_kill_rejects_zero_total_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "zero-total")
    solution = _write_overlay(tmp_path, "solution-zero", source="x = 1\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=0, failed=0, total=0, returncode=2, stderr="no tests ran")
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, outcome = validate_module.check_solution_detailed(
        task,
        "traps/crash",
        solution,
        require_visible=True,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert any("not a valid kill" in problem for problem in problems), problems
    assert outcome is hidden


def test_hidden_kill_rejects_failed_with_zero_passed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "no-passed")
    solution = _write_overlay(tmp_path, "solution-nopass", source="x = 2\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=0, failed=10, total=10, returncode=1)
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, _ = validate_module.check_solution_detailed(
        task,
        "mutants/all-failed",
        solution,
        require_visible=False,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert any("not a valid kill" in problem for problem in problems), problems


def test_hidden_kill_rejects_total_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "mismatch")
    solution = _write_overlay(tmp_path, "solution-mismatch", source="x = 3\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=3, failed=1, total=4, returncode=1)
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, _ = validate_module.check_solution_detailed(
        task,
        "traps/short-suite",
        solution,
        require_visible=True,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert any("not a valid kill" in problem for problem in problems), problems


def test_hidden_kill_rejects_collection_error_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "collect-error")
    solution = _write_overlay(tmp_path, "solution-collect", source="x = 4\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(
        passed=8,
        failed=2,
        total=10,
        returncode=1,
        stderr="ERROR collecting tests/hidden/test_extra.py",
    )
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, _ = validate_module.check_solution_detailed(
        task,
        "traps/collect-error",
        solution,
        require_visible=True,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert any("not a valid kill" in problem for problem in problems), problems


def test_hidden_kill_accepts_real_partial_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "good-kill")
    solution = _write_overlay(tmp_path, "solution-good", source="x = 5\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=9, failed=1, total=10, returncode=1)
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, _ = validate_module.check_solution_detailed(
        task,
        "traps/good",
        solution,
        require_visible=True,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert problems == []


def test_hidden_all_pass_still_reported_as_undetected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "undetected")
    solution = _write_overlay(tmp_path, "solution-undetected", source="x = 6\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=10, failed=0, total=10, returncode=0)
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems, _ = validate_module.check_solution_detailed(
        task,
        "traps/undetected",
        solution,
        require_visible=True,
        require_hidden=False,
        expected_hidden_total=10,
    )
    assert any("hidden tests did not detect the wrong solution" in p for p in problems), problems


def test_check_solution_public_signature_still_returns_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _prepared_task(tmp_path, "compat")
    solution = _write_overlay(tmp_path, "solution-compat", source="x = 7\n")
    visible = _outcome(passed=4, failed=0, total=4, returncode=0)
    hidden = _outcome(passed=10, failed=0, total=10, returncode=0)
    _patch_outcomes(monkeypatch, [visible, hidden])

    problems = validate_module.check_solution(
        task, "traps/compat", solution, require_visible=True, require_hidden=False
    )
    assert isinstance(problems, list)
    assert all(isinstance(problem, str) for problem in problems)
    assert any("did not detect" in problem for problem in problems)


# ---------------------------------------------------------------------------
# Finding 12: mutant byte-identical to trap or another mutant
# ---------------------------------------------------------------------------


def test_duplicate_mutant_vs_trap_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "dup-trap"
    task = _static_task(root)
    _write_overlay(task.traps_dir, "t1", source="VALUE = 1\n")
    _write_overlay(task.traps_dir, "t2", source="VALUE = 2\n")
    _write_overlay(task.mutants_dir, "m1", source="VALUE = 1\n")  # identical to trap t1
    _write_overlay(task.mutants_dir, "m2", source="VALUE = 3\n")
    _write_overlay(task.mutants_dir, "m3", source="VALUE = 4\n")
    hidden = task.hidden_dir / "tests" / "hidden" / "test_x.py"
    hidden.write_text("def test_a() -> None:\n    pass\n" * 8, encoding="utf-8")
    _stub_check_solution(monkeypatch)

    problems = validate_module.validate_task(task)
    assert any("byte-identical" in p and "m1" in p and "t1" in p for p in problems), problems


def test_duplicate_mutant_vs_mutant_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "dup-mutant"
    task = _static_task(root)
    _write_overlay(task.traps_dir, "t1", source="VALUE = 1\n")
    _write_overlay(task.traps_dir, "t2", source="VALUE = 2\n")
    _write_overlay(task.mutants_dir, "m1", source="VALUE = 3\n")
    _write_overlay(task.mutants_dir, "m2", source="VALUE = 4\n")
    _write_overlay(task.mutants_dir, "m3", source="VALUE = 4\n")  # identical to mutant m2
    hidden = task.hidden_dir / "tests" / "hidden" / "test_x.py"
    hidden.write_text("def test_a() -> None:\n    pass\n" * 8, encoding="utf-8")
    _stub_check_solution(monkeypatch)

    problems = validate_module.validate_task(task)
    assert any("byte-identical" in p and "m3" in p and "m2" in p for p in problems), problems


def test_distinct_mutants_not_flagged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "distinct"
    task = _static_task(root)
    _write_overlay(task.traps_dir, "t1", source="VALUE = 1\n")
    _write_overlay(task.traps_dir, "t2", source="VALUE = 2\n")
    _write_overlay(task.mutants_dir, "m1", source="VALUE = 3\n")
    _write_overlay(task.mutants_dir, "m2", source="VALUE = 4\n")
    _write_overlay(task.mutants_dir, "m3", source="VALUE = 5\n")
    hidden = task.hidden_dir / "tests" / "hidden" / "test_x.py"
    hidden.write_text("def test_a() -> None:\n    pass\n" * 8, encoding="utf-8")
    _stub_check_solution(monkeypatch)

    problems = validate_module.validate_task(task)
    assert not any("byte-identical" in p for p in problems), problems


# ---------------------------------------------------------------------------
# Finding 14: >= 8 hidden tests required
# ---------------------------------------------------------------------------


def test_hidden_test_counter_counts_python_functions(tmp_path: Path) -> None:
    task = _task(tmp_path / "hidden-count")
    hidden = task.hidden_dir / "tests" / "hidden"
    hidden.mkdir(parents=True)
    (hidden / "test_a.py").write_text(
        "def test_one(): pass\ndef test_two(): pass\n", encoding="utf-8"
    )
    (hidden / "test_b.py").write_text("def test_three(): pass\n", encoding="utf-8")
    (hidden / "notes.txt").write_text("def test_fake(): pass\n", encoding="utf-8")

    assert validate_module.count_hidden_tests(task) == 3


def test_hidden_test_counter_counts_typescript_calls(tmp_path: Path) -> None:
    task = _task(tmp_path / "hidden-ts", language=Language.TYPESCRIPT)
    hidden = task.hidden_dir / "tests" / "hidden"
    hidden.mkdir(parents=True)
    (hidden / "x.test.ts").write_text(
        "test('a', () => {});\nit('b', () => {});\n", encoding="utf-8"
    )
    (hidden / "readme.txt").write_text("it('c', () => {});\n", encoding="utf-8")

    assert validate_module.count_hidden_tests(task) == 2


def test_too_few_hidden_tests_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "few-hidden"
    task = _static_task(root)
    _write_overlay(task.traps_dir, "t1", source="VALUE = 1\n")
    _write_overlay(task.traps_dir, "t2", source="VALUE = 2\n")
    _write_overlay(task.mutants_dir, "m1", source="VALUE = 3\n")
    _write_overlay(task.mutants_dir, "m2", source="VALUE = 4\n")
    _write_overlay(task.mutants_dir, "m3", source="VALUE = 5\n")
    hidden = task.hidden_dir / "tests" / "hidden" / "test_x.py"
    hidden.write_text(
        "def test_one(): pass\ndef test_two(): pass\ndef test_three(): pass\n", encoding="utf-8"
    )
    _stub_check_solution(monkeypatch)

    problems = validate_module.validate_task(task)
    assert any("at least 8" in p and "3" in p for p in problems), problems


def test_eight_hidden_tests_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "enough-hidden"
    task = _static_task(root)
    _write_overlay(task.traps_dir, "t1", source="VALUE = 1\n")
    _write_overlay(task.traps_dir, "t2", source="VALUE = 2\n")
    _write_overlay(task.mutants_dir, "m1", source="VALUE = 3\n")
    _write_overlay(task.mutants_dir, "m2", source="VALUE = 4\n")
    _write_overlay(task.mutants_dir, "m3", source="VALUE = 5\n")
    hidden = task.hidden_dir / "tests" / "hidden" / "test_x.py"
    hidden.write_text("".join(f"def test_{i}(): pass\n" for i in range(8)), encoding="utf-8")
    _stub_check_solution(monkeypatch)

    problems = validate_module.validate_task(task)
    assert not any("at least 8" in p for p in problems), problems


# ---------------------------------------------------------------------------
# Finding 18: protected_files violation helper + implementation_files parsing
# ---------------------------------------------------------------------------


def test_protected_file_modification_detected(tmp_path: Path) -> None:
    task = _task(tmp_path / "pristine", protected=("src/keep.py",))
    pristine = task.root
    pristine_workspace = pristine / "workspace" / "src" / "keep.py"
    pristine_workspace.parent.mkdir(parents=True)
    pristine_workspace.write_bytes(b"ORIGINAL\n")

    current = tmp_path / "agent-workspace"
    modified = current / "src" / "keep.py"
    modified.parent.mkdir(parents=True)
    modified.write_bytes(b"TAMPERED\n")

    violations = validate_module.protected_file_violations(task, pristine, current)
    assert any("protected file modified: src/keep.py" in v for v in violations), violations


def test_protected_file_unchanged_and_deleted(tmp_path: Path) -> None:
    task = _task(tmp_path / "pristine", protected=("src/keep.py",))
    pristine = task.root
    pristine_file = pristine / "workspace" / "src" / "keep.py"
    pristine_file.parent.mkdir(parents=True)
    pristine_file.write_bytes(b"ORIGINAL\n")

    same = tmp_path / "same"
    same_file = same / "src" / "keep.py"
    same_file.parent.mkdir(parents=True)
    same_file.write_bytes(b"ORIGINAL\n")
    assert validate_module.protected_file_violations(task, pristine, same) == []

    deleted = tmp_path / "deleted"
    deleted.mkdir()
    violations = validate_module.protected_file_violations(task, pristine, deleted)
    assert any("protected file deleted: src/keep.py" in v for v in violations), violations


def test_implementation_files_parsed_from_task_yaml() -> None:
    raw = dict(_VALID_RAW)
    raw["implementation_files"] = ["src/a.py", "src/b.py"]
    task, errors = validate_task_schema(raw, Path("demo"))
    assert errors == []
    assert task is not None
    assert task.implementation_files == ("src/a.py", "src/b.py")


def test_implementation_files_defaults_to_empty() -> None:
    task, errors = validate_task_schema(dict(_VALID_RAW), Path("demo"))
    assert errors == []
    assert task is not None
    assert task.implementation_files == ()


def test_implementation_files_bad_type_rejected() -> None:
    raw = dict(_VALID_RAW)
    raw["implementation_files"] = "src/a.py"
    task, errors = validate_task_schema(raw, Path("demo"))
    assert task is None
    assert any("implementation_files must be a list of strings" in e for e in errors), errors


def test_implementation_files_survives_yaml_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    raw = dict(_VALID_RAW)
    raw["implementation_files"] = ["src/a.py"]
    (root / "task.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    parsed: object = yaml.safe_load((root / "task.yaml").read_text(encoding="utf-8"))
    loaded = validate_task_schema(parsed, root)
    assert loaded[1] == []
    assert loaded[0] is not None
    assert loaded[0].implementation_files == ("src/a.py",)
