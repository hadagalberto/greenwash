"""Tests for agent adapters."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from conftest import (
    install_fake_exe,
    write_fake_cli,
    write_fake_docker,
    write_script,
    write_step,
)
from greenwash.adapters import (
    AdapterUnavailableError,
    AiderAdapter,
    ClaudeCodeAdapter,
    CodexAdapter,
    CommandAdapter,
    OpenCodeAdapter,
    ScriptedAgentAdapter,
    available_adapters,
    make_prompt,
    parse_cli_output,
    resolve_adapter,
)
from greenwash.fake_agent import FakeScriptError, load_fake_script
from greenwash.models import Task
from greenwash.sandbox import DockerSandbox


def test_make_prompt_contains_spec_and_required_instruction(crc_task: Task) -> None:
    prompt = make_prompt(crc_task)
    assert "CRC-32 check values" in prompt
    assert "STATUS: DONE" in prompt
    assert "run the tests" in prompt


def test_command_adapter_runs_template_and_parses_claim(tmp_path: Path) -> None:
    agent = tmp_path / "fake_agent.py"
    agent.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "workdir = Path(sys.argv[1])\n"
        "prompt = Path(sys.argv[2]).read_text()\n"
        "(workdir / 'agent-ran.txt').write_text(prompt[:40])\n"
        "print('fake agent finished')\n"
        "print('STATUS: DONE')\n",
        encoding="utf-8",
    )
    adapter = CommandAdapter(
        f'{sys.executable} "{{workdir}}/{agent.name}" "{{workdir}}" "{{prompt_file}}"'
    )
    result = adapter.run(tmp_path, "solve it", 30)
    assert (tmp_path / "agent-ran.txt").read_text(encoding="utf-8") == "solve it"
    assert result.claim.certain is True
    assert str(result.claim.status) == "DONE"
    assert result.exit_code == 0
    assert result.adapter == "command"


def test_command_adapter_validates_template() -> None:
    with pytest.raises(AdapterUnavailableError):
        CommandAdapter("")
    with pytest.raises(AdapterUnavailableError):
        CommandAdapter("echo hi")


def test_command_adapter_reports_missing_command() -> None:
    with pytest.raises(AdapterUnavailableError, match="requires --agent-cmd"):
        resolve_adapter("command")


def test_command_adapter_reports_unknown_adapter() -> None:
    with pytest.raises(AdapterUnavailableError, match="not available"):
        resolve_adapter("definitely-not-an-adapter")


def test_scripted_adapter_applies_steps(tmp_path: Path) -> None:
    path = write_script(
        tmp_path,
        "honest.json",
        {"steps": [write_step("src/new.txt", "hello")], "status": "DONE", "summary": "done"},
    )
    adapter = resolve_adapter("scripted", script_path=path)
    assert isinstance(adapter, ScriptedAgentAdapter)
    result = adapter.run(tmp_path, "prompt", 30)
    assert (tmp_path / "src" / "new.txt").read_text(encoding="utf-8") == "hello"
    assert str(result.claim.status) == "DONE"
    assert "STATUS: DONE" in result.transcript


def test_scripted_adapter_requires_script() -> None:
    with pytest.raises(AdapterUnavailableError, match="requires --script"):
        resolve_adapter("scripted")


def test_fake_script_validation(tmp_path: Path) -> None:
    bad = write_script(tmp_path, "bad.json", {"steps": [{"op": "explode", "path": "x"}]})
    with pytest.raises(FakeScriptError, match="op must be"):
        load_fake_script(bad)

    traversal = write_script(
        tmp_path, "traversal.json", {"steps": [write_step("../escape.txt", "x")]}
    )
    script = load_fake_script(traversal)
    adapter = ScriptedAgentAdapter(script)
    with pytest.raises(FakeScriptError, match="escapes the workspace"):
        adapter.run(tmp_path, "prompt", 30)

    missing = tmp_path / "missing.json"
    with pytest.raises(FakeScriptError, match="cannot read"):
        load_fake_script(missing)


def test_parse_cli_output_handles_json_jsonl_and_raw_text() -> None:
    parsed = parse_cli_output(
        '{"result":"STATUS: DONE","usage":{"input_tokens":11,"output_tokens":2},'
        '"total_cost_usd":0.25}',
        ("result", "content"),
    )
    assert parsed.text == "STATUS: DONE"
    assert (parsed.tokens_in, parsed.tokens_out, parsed.cost_usd) == (11, 2, 0.25)

    stream = (
        '{"text":"first"}\n'
        '{"text":"STATUS: DONE","usage":{"prompt_tokens":5,"completion_tokens":1},'
        '"cost_usd":0.01}\n'
        "broken line\n"
    )
    streamed = parse_cli_output(stream, ("text",))
    assert streamed.text == "first\nSTATUS: DONE"
    assert (streamed.tokens_in, streamed.tokens_out, streamed.cost_usd) == (5, 1, 0.01)

    raw = parse_cli_output("plain STATUS: DONE", ("content",))
    assert raw.text == "plain STATUS: DONE" and raw.tokens_in == 0
    assert parse_cli_output("   ", ("content",)).text == ""


@pytest.mark.parametrize(
    ("name", "cls", "stdout", "argv_tail", "tokens_in", "tokens_out", "cost"),
    [
        (
            "opencode",
            OpenCodeAdapter,
            '{"content":"STATUS: DONE","usage":{"input_tokens":100,"output_tokens":20}}',
            # Finding 9/10: model flag added; multi-line prompt goes via stdin.
            ["run", "--model", "model-opencode", "--format", "json"],
            100,
            20,
            0.0,
        ),
        (
            "claude-code",
            ClaudeCodeAdapter,
            '{"result":"STATUS: DONE","usage":{"input_tokens":7,"output_tokens":3},'
            '"total_cost_usd":0.42}',
            ["-p", "--model", "model-claude-code", "--output-format", "json"],
            7,
            3,
            0.42,
        ),
        (
            "aider",
            AiderAdapter,
            "edited files\nSTATUS: DONE\n",
            # Finding 6: the multi-line prompt goes to a transient file, never
            # in argv (npm .cmd launchers truncate at the first newline).
            ["--model", "model-aider", "--message-file", None, "--yes", "--no-auto-commits"],
            0,
            0,
            0.0,
        ),
        (
            "codex",
            CodexAdapter,
            '{"text":"part"}\n{"text":"STATUS: DONE","usage":'
            '{"prompt_tokens":9,"completion_tokens":4},"cost_usd":0.01}',
            # Finding 6: codex reads the prompt from stdin via `exec -`.
            ["exec", "-m", "model-codex", "--json", "-"],
            9,
            4,
            0.01,
        ),
    ],
)
def test_cli_adapters_run_fake_executables(
    name: str,
    cls: type,
    stdout: str,
    argv_tail: list[str],
    tokens_in: int,
    tokens_out: int,
    cost: float,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "cli.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CLI_LOG", str(log))
    # claude-code adapters invoke the `claude` binary; all others use their name.
    executable_name = "claude" if name == "claude-code" else name
    write_fake_cli(bin_dir, executable_name, stdout, stderr="notice", exit_code=0)
    work = tmp_path / "work"
    work.mkdir()

    adapter = resolve_adapter(name, model=f"model-{name}")
    assert isinstance(adapter, cls)
    result = adapter.run(work, "solve it", 30)
    assert result.adapter == name and result.model == f"model-{name}"
    assert str(result.claim.status) == "DONE" and result.claim.certain is True
    assert "STATUS: DONE" in result.transcript and "notice" in result.transcript
    assert (result.tokens_in, result.tokens_out, result.cost_usd) == (
        tokens_in,
        tokens_out,
        cost,
    )
    assert result.exit_code == 0 and result.timed_out is False
    recorded = json.loads(log.read_text(encoding="utf-8"))
    if name == "aider":
        # Finding 6: the path is generated per run; verify the surrounding flags
        # and that the file really contains the whole prompt.
        argv = recorded["argv"]
        assert argv[:3] == ["--model", "model-aider", "--message-file"]
        assert argv[4:] == ["--yes", "--no-auto-commits"]
        assert Path(argv[3]).name.startswith(".greenwash-prompt-")
        assert not Path(argv[3]).exists()  # transient prompt file cleaned up
    else:
        assert recorded["argv"] == argv_tail
    assert recorded["cwd"] == str(work)


def test_cli_adapters_are_reported_unavailable_when_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "empty").mkdir()
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    statuses = available_adapters()
    for name in ("opencode", "claude-code", "aider", "codex"):
        assert statuses[name] is False
        with pytest.raises(AdapterUnavailableError, match="not available"):
            resolve_adapter(name)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert available_adapters()["builtin"] is False
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert available_adapters()["builtin"] is True
    assert available_adapters()["command"] is True


def test_cli_adapter_reports_failure_and_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "cli.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CLI_LOG", str(log))
    write_fake_cli(bin_dir, "opencode", "partial status: failed", stderr="boom", exit_code=4)
    adapter = resolve_adapter("opencode")
    result = adapter.run(tmp_path, "go", 30)
    assert result.exit_code == 4
    assert str(result.claim.status) == "FAILED"
    assert result.claim.certain is False
    assert "boom" in result.transcript

    slow = bin_dir / "slow_impl.py"
    slow.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    install_fake_exe(bin_dir, "claude", slow)
    timed = resolve_adapter("claude-code").run(tmp_path, "go", 1)
    assert timed.timed_out is True and timed.exit_code == 130
    assert "AGENT TIMEOUT after 1s" in timed.transcript


def test_command_adapter_through_docker_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "docker.json"
    docker = write_fake_docker(tmp_path, log)
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
    work = tmp_path / "work"
    work.mkdir()
    (work / "agent.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "d = Path(sys.argv[1])\n"
        "(d / 'agent-ran.txt').write_text(Path(sys.argv[2]).read_text())\n"
        "print('STATUS: DONE')\n",
        encoding="utf-8",
    )
    adapter = resolve_adapter(
        "command",
        command=f'{sys.executable} "{{workdir}}/agent.py" "{{workdir}}" "{{prompt_file}}"',
        sandbox=DockerSandbox("unit:1", executable=str(docker)),
    )
    result = adapter.run(work, "solve it", 30)
    assert (work / "agent-ran.txt").read_text(encoding="utf-8") == "solve it"
    assert str(result.claim.status) == "DONE"
    assert list(work.glob(".greenwash-prompt-*")) == []
    calls = json.loads(log.read_text(encoding="utf-8"))
    assert len(calls) == 1
    assert f"{work}:/work" in calls[0]
    assert "unit:1" in calls[0]


def test_cli_adapter_through_docker_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cli_log = tmp_path / "cli.json"
    docker_log = tmp_path / "docker.json"
    docker = write_fake_docker(tmp_path, docker_log)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CLI_LOG", str(cli_log))
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(docker_log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
    write_fake_cli(bin_dir, "opencode", '{"content":"STATUS: DONE"}')
    work = tmp_path / "work"
    work.mkdir()
    adapter = resolve_adapter("opencode", sandbox=DockerSandbox("unit:1", executable=str(docker)))
    result = adapter.run(work, "solve it", 30)
    assert str(result.claim.status) == "DONE"
    calls = json.loads(docker_log.read_text(encoding="utf-8"))
    assert len(calls) == 1 and "opencode" in calls[0]
    assert f"{work}:/work" in calls[0]
