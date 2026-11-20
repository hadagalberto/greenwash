"""Tests for agent adapters."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import write_script, write_step
from greenwash.adapters import (
    AdapterUnavailableError,
    CommandAdapter,
    ScriptedAgentAdapter,
    make_prompt,
    resolve_adapter,
)
from greenwash.fake_agent import FakeScriptError, load_fake_script
from greenwash.models import Task


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
        resolve_adapter("opencode")


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
