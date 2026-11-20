"""Tests for the command-line interface."""

from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

import pytest

from conftest import source_of, write_fake_docker, write_script, write_step
from fake_openai_server import FakeOpenAIServer, assistant_turn
from greenwash.cli import main
from greenwash.models import Task


def test_cli_validate_tasks_success(tasks_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["validate-tasks", "--tasks", str(tasks_dir)])
    assert code == 0
    # Milestone 3 expanded the suite from 3 to 20 tasks; the old string was a
    # snapshot of milestone 1, not a behavioural requirement of the CLI.
    assert "validated 20 task(s)" in capsys.readouterr().out


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


def test_cli_run_builtin_against_local_fake_server(
    crc_task: Task,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with FakeOpenAIServer(
        [assistant_turn(content="STATUS: DONE\nno files changed", tokens_in=100, tokens_out=20)]
    ) as server:
        code = main(
            [
                "run",
                "--agent",
                "builtin",
                "--model",
                "gpt-4o-mini",
                "--base-url",
                server.url,
                "--tasks",
                str(crc_task.root.parent),
                "--glob",
                crc_task.id,
                "--repeat",
                "1",
                "--out",
                str(tmp_path / "out"),
            ]
        )
        assert len(server.requests) == 1
    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["overall"]["attempts"] == 1
    record = json.loads((tmp_path / "out" / "results.jsonl").read_text(encoding="utf-8").strip())
    assert record["tokens_in"] == 100 and record["tokens_out"] == 20
    assert record["cost_usd"] == pytest.approx(100 / 1_000_000 * 0.15 + 20 / 1_000_000 * 0.6)
    assert record["greenwash"] is True  # claimed done without changing the implementation


def test_cli_run_with_command_adapter(
    crc_task: Task, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = tmp_path / "agent.py"
    script.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1], 'agent-ran.txt').write_text(Path(sys.argv[2]).read_text())\n"
        "print('STATUS: DONE')\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    code = main(
        [
            "run",
            "--agent",
            "command",
            "--agent-cmd",
            f'{sys.executable} "{script}" "{{workdir}}" "{{prompt_file}}"',
            "--tasks",
            str(crc_task.root.parent),
            "--glob",
            crc_task.id,
            "--out",
            str(out),
        ]
    )
    assert code == 0
    record = json.loads((out / "results.jsonl").read_text(encoding="utf-8").strip())
    assert str(record["claim"]["status"]) == "DONE"
    printed = json.loads(capsys.readouterr().out)
    assert printed["overall"]["attempts"] == 1


def test_cli_run_with_docker_sandbox(
    crc_task: Task,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
    docker_log = tmp_path / "docker.json"
    write_fake_docker(tmp_path, docker_log)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(docker_log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
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
            "--sandbox",
            "docker",
            "--sandbox-image",
            "unit:1",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["overall"]["hidden_pass_rate"] == 1.0
    calls = json.loads(docker_log.read_text(encoding="utf-8"))
    assert calls
    assert all(any(":/work" in arg for arg in call) for call in calls)
    assert all("unit:1" in call for call in calls)


def test_cli_rejects_bad_sandbox_and_step_limit(
    tasks_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(["run", "--agent", "scripted", "--tasks", str(tasks_dir), "--sandbox", "podman"]) == 2
    )
    assert "unknown sandbox" in capsys.readouterr().out
    assert (
        main(
            [
                "run",
                "--agent",
                "scripted",
                "--tasks",
                str(tasks_dir),
                "--max-steps",
                "0",
            ]
        )
        == 2
    )
    assert "max-steps" in capsys.readouterr().out
    assert main(["run", "--agent", "builtin", "--tasks", str(tasks_dir)]) == 2
    assert "model" in capsys.readouterr().out


def test_cli_rejects_invalid_price_table(
    crc_task: Task, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "prices.json"
    bad.write_text('{"version": 99, "models": {}}', encoding="utf-8")
    code = main(
        [
            "run",
            "--agent",
            "builtin",
            "--model",
            "gpt-4o-mini",
            "--price-table",
            str(bad),
            "--tasks",
            str(crc_task.root.parent),
            "--glob",
            crc_task.id,
        ]
    )
    assert code == 2
    assert "version" in capsys.readouterr().out
