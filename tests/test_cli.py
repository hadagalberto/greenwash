"""Tests for the command-line interface."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

from conftest import source_of, write_script, write_step
from greenwash.cli import main
from greenwash.models import Task


def test_cli_validate_tasks_success(tasks_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["validate-tasks", "--tasks", str(tasks_dir)])
    assert code == 0
    assert "validated 3 task(s)" in capsys.readouterr().out


def test_cli_validate_tasks_failure(
    tasks_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import shutil

    root = tmp_path / "crc32-check"
    shutil.copytree(tasks_dir / "crc32-check", root)
    (root / "reference" / "src" / "checksum.py").write_text(
        "def crc32(data):\n    return -1\n", encoding="utf-8"
    )
    code = main(["validate-tasks", "--tasks", str(tmp_path)])
    assert code == 1
    assert "FAIL:" in capsys.readouterr().out


def test_cli_validate_tasks_no_tasks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate-tasks", "--tasks", str(tmp_path)]) == 2
    assert "no tasks found" in capsys.readouterr().out


def test_cli_run_with_scripted_agent(
    crc_task: Task, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = write_script(
        tmp_path,
        "honest.json",
        {
            "steps": [
                write_step(
                    "src/checksum.py",
                    source_of(crc_task, "reference", "src/checksum.py"),
                )
            ],
            "status": "DONE",
            "summary": "all tests pass",
        },
    )
    out = tmp_path / "out"
    code = main(
        [
            "run",
            "--agent",
            "scripted",
            "--script",
            str(script),
            "--tasks",
            str(crc_task.root.parent),
            "--glob",
            crc_task.id,
            "--repeat",
            "2",
            "--jobs",
            "2",
            "--timeout",
            "60",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["overall"]["hidden_pass_rate"] == 1.0
    assert Path(printed["results"]).is_file()
    assert (out / "summary.json").is_file()


def test_cli_run_rejects_bad_arguments(tasks_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--agent", "unknown", "--tasks", str(tasks_dir)]) == 2
    assert "not available" in capsys.readouterr().out
    assert main(["run", "--agent", "scripted", "--tasks", str(tasks_dir), "--repeat", "0"]) == 2
    assert "repeat" in capsys.readouterr().out


def test_cli_reports_task_load_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "task.yaml").write_text("id: [broken\n", encoding="utf-8")
    (broken / "broken").mkdir()
    with pytest.raises(SystemExit, match="invalid task|invalid YAML"):
        main(["validate-tasks", "--tasks", str(broken.parent)])
    capsys.readouterr()


def test_module_entry_point(tasks_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["greenwash", "validate-tasks", "--tasks", str(tasks_dir)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("greenwash", run_name="__main__")
    assert exc.value.code == 0
