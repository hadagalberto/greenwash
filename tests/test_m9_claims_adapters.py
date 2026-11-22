"""Regression tests for milestone-9 claim parsing and adapter findings.

Every expectation here is derived by hand from SPEC.md and the finding reports,
not from the current implementation. Tests were written before the fixes.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import pytest

from conftest import install_fake_exe
from greenwash.adapters import (
    AgentAdapter,
    AiderAdapter,
    ClaudeCodeAdapter,
    CodexAdapter,
    CommandAdapter,
    OpenCodeAdapter,
    ScriptedAgentAdapter,
    parse_cli_output,
)
from greenwash.claims import parse_claim
from greenwash.fake_agent import FakeScript
from greenwash.models import ClaimStatus
from greenwash.sandbox import CommandOutput, LocalSandbox


def _install_recording_cli(bin_dir: Path, name: str, stdout: str, log: Path) -> None:
    """Install a fake CLI whose absolute log path is baked into the script.

    Sandboxes deliberately forward only a small allow-list of host variables,
    so test doubles cannot rely on a custom environment variable to find their
    log file.
    """
    script = bin_dir / f"{name}_rec_impl.py"
    script.write_text(
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"record = Path({str(log)!r})\n"
        "record.write_text(\n"
        "    json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}),\n"
        "    encoding='utf-8',\n"
        ")\n"
        f"sys.stdout.write({stdout!r})\n",
        encoding="utf-8",
    )
    install_fake_exe(bin_dir, name, script)


# ---------------------------------------------------------------------------
# Finding 8: claim parsing must inspect only the agent's FINAL message
# ---------------------------------------------------------------------------


def test_status_line_must_be_final_even_when_earlier_status_says_done() -> None:
    claim = parse_claim(
        "Fixed it.\nSTATUS: DONE\n\nWait - I re-ran and 2 tests still fail; I could not fix them."
    )
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence


def test_status_mentioned_inside_a_sentence_is_not_a_status_line() -> None:
    claim = parse_claim(
        "spec says:\nSTATUS: DONE or STATUS: FAILED\nI ran out of time and could not finish."
    )
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence


def test_mixed_failure_and_success_hints_are_failure_not_done() -> None:
    """Round-3 item 7: this assertion used to expect DONE, which was the bug.

    A message that mentions both a failure and a success without a STATUS line
    is ambiguous; it must be reported pessimistically as FAILED, never DONE.
    """
    claim = parse_claim("Initially the tests failed. I fixed the off-by-one. All tests pass now.")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence


def test_failure_hint_inside_another_word_does_not_match() -> None:
    claim = parse_claim("The api failed to round-trip; fixed. All tests pass.")
    assert claim.status is ClaimStatus.DONE
    assert claim.certain is False
    assert claim.evidence


def test_final_message_is_not_dragged_down_by_earlier_tool_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Round-2 finding 12: use a real builtin transcript, not a hand-picked string.

    On fb305b7 the builtin adapter parsed the whole transcript, so tool output
    containing "incomplete" dragged the final DONE claim down to FAILED.
    """
    from fake_openai_server import FakeOpenAIServer, assistant_turn, tool_call
    from greenwash.adapters import resolve_adapter

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    (tmp_path / "notes.txt").write_text("incomplete draft\n", encoding="utf-8")
    responses = [
        assistant_turn(
            calls=[tool_call("read_file", {"path": "notes.txt"}, "call-1")],
            tokens_in=10,
            tokens_out=2,
        ),
        assistant_turn(content="All tests pass. Task complete.", tokens_in=10, tokens_out=2),
    ]
    with FakeOpenAIServer(responses) as server:
        adapter = resolve_adapter("builtin", model="gpt-4o-mini", base_url=server.url)
        result = adapter.run(tmp_path, "go", 30)
    assert "incomplete" in result.transcript
    assert result.claim.status is ClaimStatus.DONE
    assert result.claim.certain is False
    assert result.claim.evidence


def test_negated_done_and_red_tests_are_failed() -> None:
    claim = parse_claim("I am not yet done; tests are red.")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence


def test_markdown_emphasis_around_status_is_stripped() -> None:
    claim = parse_claim("**STATUS: DONE**")
    assert claim.status is ClaimStatus.DONE
    assert claim.certain is True


def test_markdown_quote_before_status_is_stripped() -> None:
    claim = parse_claim("> STATUS: FAILED\n")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is True


@pytest.mark.parametrize(
    "line",
    ["*STATUS: DONE*", "_STATUS: DONE_", "- STATUS: DONE", "`STATUS: DONE`"],
)
def test_other_markdown_markers_around_status_are_stripped(line: str) -> None:
    claim = parse_claim(line)
    assert claim.status is ClaimStatus.DONE
    assert claim.certain is True


@pytest.mark.parametrize(
    "hint",
    [
        "could not fix",
        "could not finish",
        "ran out of time",
        "not yet done",
        "tests are red",
        "still fail",
    ],
)
def test_added_failure_hints_are_recognised_uncertain(hint: str) -> None:
    claim = parse_claim(f"The work is blocked: {hint}.")
    assert claim.status is ClaimStatus.FAILED
    assert claim.certain is False
    assert claim.evidence == hint


def test_final_text_document_of_jsonl_is_the_final_message() -> None:
    parsed = parse_cli_output(
        '{"text":"incomplete tool note"}\n{"text":"All tests pass. Task complete."}',
        ("text",),
    )
    assert parsed.text == "incomplete tool note\nAll tests pass. Task complete."
    assert parsed.final_message == "All tests pass. Task complete."


def test_cli_adapter_parses_final_message_not_full_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "cli.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    _install_recording_cli(
        bin_dir,
        "opencode",
        '{"text":"tests failed"}\n{"text":"All tests pass. Task complete."}',
        log,
    )
    work = tmp_path / "work"
    work.mkdir()
    adapter = OpenCodeAdapter(model="m", executable="opencode")
    result = adapter.run(work, "solve it", 30)
    assert result.final_message == "All tests pass. Task complete."
    assert result.claim.status is ClaimStatus.DONE
    assert result.claim.certain is False
    assert "tests failed" in result.transcript
    assert result.claim.evidence == parse_claim(result.final_message).evidence


def test_command_and_scripted_adapters_expose_whole_stdout_as_final_message(
    tmp_path: Path,
) -> None:
    agent = tmp_path / "agent.py"
    agent.write_text("print('STATUS: DONE')\n", encoding="utf-8")
    command = CommandAdapter(f'python "{agent}" "{{workdir}}" "{{prompt_file}}"')
    command_result = command.run(tmp_path, "solve it", 30)
    assert command_result.final_message == command_result.transcript
    assert command_result.claim.status is ClaimStatus.DONE

    script = FakeScript(
        steps=(),
        status=ClaimStatus.DONE,
        summary="all good",
    )
    scripted = ScriptedAgentAdapter(script)
    scripted_result = scripted.run(tmp_path, "solve it", 30)
    assert scripted_result.final_message == scripted_result.transcript
    assert scripted_result.claim.status is ClaimStatus.DONE


# ---------------------------------------------------------------------------
# Finding 9: --model must be forwarded to every CLI adapter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("factory", "flag", "earlier_flag"),
    [
        (lambda m: OpenCodeAdapter(model=m), "--model", "--format"),
        (lambda m: ClaudeCodeAdapter(model=m), "--model", "--output-format"),
        # Finding 6: aider receives the prompt through --message-file, not --message.
        (lambda m: AiderAdapter(model=m), "--model", "--message-file"),
        (lambda m: CodexAdapter(model=m), "-m", "--json"),
    ],
)
def test_cli_adapters_pass_model_flag(
    factory: Callable[[str], AgentAdapter],
    flag: str,
    earlier_flag: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "cli.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    _install_recording_cli(bin_dir, "opencode", '{"content":"STATUS: DONE"}', log)
    _install_recording_cli(bin_dir, "claude", '{"result":"STATUS: DONE"}', log)
    _install_recording_cli(bin_dir, "aider", "STATUS: DONE\n", log)
    _install_recording_cli(bin_dir, "codex", '{"text":"STATUS: DONE"}', log)
    work = tmp_path / "work"
    work.mkdir()

    adapter = factory("model-under-test")
    adapter.run(work, "solve it", 30)
    argv = json.loads(log.read_text(encoding="utf-8"))["argv"]
    assert flag in argv
    assert argv[argv.index(flag) + 1] == "model-under-test"
    assert argv.index(flag) < argv.index(earlier_flag)


@pytest.mark.parametrize(
    ("factory", "flag"),
    [
        (lambda m: OpenCodeAdapter(model=m), "--model"),
        (lambda m: ClaudeCodeAdapter(model=m), "--model"),
        (lambda m: AiderAdapter(model=m), "--model"),
        (lambda m: CodexAdapter(model=m), "-m"),
    ],
)
def test_empty_model_omits_model_flag(
    factory: Callable[[str], AgentAdapter],
    flag: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "cli.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    _install_recording_cli(bin_dir, "opencode", '{"content":"STATUS: DONE"}', log)
    _install_recording_cli(bin_dir, "claude", '{"result":"STATUS: DONE"}', log)
    _install_recording_cli(bin_dir, "aider", "STATUS: DONE\n", log)
    _install_recording_cli(bin_dir, "codex", '{"text":"STATUS: DONE"}', log)
    work = tmp_path / "work"
    work.mkdir()

    adapter = factory("")
    adapter.run(work, "solve it", 30)
    argv = json.loads(log.read_text(encoding="utf-8"))["argv"]
    assert "--model" not in argv
    assert "-m" not in argv
    assert flag not in argv


# ---------------------------------------------------------------------------
# Finding 10: multi-line prompt must arrive intact via stdin
# ---------------------------------------------------------------------------


class _StdinSandbox(LocalSandbox):
    """LocalSandbox variant that really feeds ``input_text`` to the child."""

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
        env_extra: Mapping[str, str] | None = None,
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput:
        completed = subprocess.run(
            list(argv),
            cwd=str(workdir),
            env=self._env(env_extra),
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
        return CommandOutput(completed.stdout, completed.stderr, completed.returncode, False)


@pytest.mark.parametrize(
    ("name", "factory"),
    [
        ("opencode", lambda m, s: OpenCodeAdapter(model=m, sandbox=s)),
        ("claude", lambda m, s: ClaudeCodeAdapter(model=m, sandbox=s)),
    ],
)
def test_multiline_prompt_reaches_cli_via_stdin(
    name: str,
    factory: Callable[[str, LocalSandbox], AgentAdapter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "stdin.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    script = bin_dir / f"{name}_stdin_impl.py"
    script.write_text(
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"record = Path({str(log)!r})\n"
        "record.write_text(\n"
        "    json.dumps({'stdin': sys.stdin.read(), 'argv': sys.argv[1:]}),\n"
        "    encoding='utf-8',\n"
        ")\n"
        'sys.stdout.write(\'{"content":"STATUS: DONE"}\')\n',
        encoding="utf-8",
    )
    install_fake_exe(bin_dir, name, script)
    work = tmp_path / "work"
    work.mkdir()
    prompt = "line one\nline two with spaces\nline three"

    adapter = factory("model-x", _StdinSandbox())
    result = adapter.run(work, prompt, 30)
    assert result.claim.status is ClaimStatus.DONE
    recorded = json.loads(log.read_text(encoding="utf-8"))
    assert recorded["stdin"] == prompt
    assert prompt not in recorded["argv"]
