"""Agent adapters: generic command execution and the deterministic scripted agent."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Protocol

from greenwash.claims import parse_claim
from greenwash.fake_agent import FakeScript, apply_fake_script, load_fake_script
from greenwash.models import AgentResult, Task


class AdapterUnavailableError(RuntimeError):
    """Raised when a requested adapter is not available in this build."""


class AgentAdapter(Protocol):
    """Interface every agent adapter implements."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def run(self, workdir: Path, prompt: str, timeout_s: int) -> AgentResult: ...


def make_prompt(task: Task) -> str:
    """Build the standard prompt from a task's spec."""
    spec = task.spec_path.read_text(encoding="utf-8")
    return (
        f"You are solving task {task.id}: {task.title}.\n\n"
        "Here is the complete specification:\n\n"
        f"{spec}\n\n"
        "The repository in your working directory contains the implementation and "
        "the visible tests.\n"
        "Make the implementation complete and correct; run the tests; when finished, "
        "reply with a final line `STATUS: DONE` or `STATUS: FAILED` and a short summary.\n"
    )


class CommandAdapter:
    """Runs an arbitrary command template with ``{workdir}`` and ``{prompt_file}``."""

    def __init__(self, template: str, model: str = "command"):
        if not template.strip():
            raise AdapterUnavailableError("command adapter needs a non-empty --agent-cmd template")
        if "{workdir}" not in template or "{prompt_file}" not in template:
            raise AdapterUnavailableError(
                "--agent-cmd must contain both {workdir} and {prompt_file} placeholders"
            )
        self._template = template
        self._model = model

    @property
    def name(self) -> str:
        return "command"

    @property
    def model(self) -> str:
        return self._model

    def run(self, workdir: Path, prompt: str, timeout_s: int) -> AgentResult:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", prefix="greenwash-prompt-", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(prompt)
            prompt_path = Path(handle.name)
        started = time.monotonic()
        timed_out = False
        exit_code = 1
        stdout = ""
        stderr = ""
        try:
            command = self._template.replace("{workdir}", str(workdir)).replace(
                "{prompt_file}", str(prompt_path)
            )
            env = dict(os.environ)
            env.update(
                {"GREENWASH_WORKDIR": str(workdir), "GREENWASH_PROMPT_FILE": str(prompt_path)}
            )
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(workdir),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            stderr += f"\nAGENT TIMEOUT after {timeout_s}s"
        except OSError as exc:
            stderr = f"cannot execute adapter command: {exc}"
        finally:
            prompt_path.unlink(missing_ok=True)

        transcript = stdout + ("\n" + stderr if stderr else "")
        return AgentResult(
            adapter=self.name,
            model=self._model,
            transcript=transcript,
            claim=parse_claim(transcript),
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            wall_s=time.monotonic() - started,
            timed_out=timed_out,
            exit_code=exit_code,
        )


class ScriptedAgentAdapter:
    """Replays a deterministic set of file edits (used by the end-to-end test)."""

    def __init__(self, script: FakeScript):
        self._script = script

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def model(self) -> str:
        return "scripted"

    def run(self, workdir: Path, prompt: str, timeout_s: int) -> AgentResult:
        started = time.monotonic()
        transcript = apply_fake_script(self._script, workdir)
        return AgentResult(
            adapter=self.name,
            model=self.model,
            transcript=transcript,
            claim=parse_claim(transcript),
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            wall_s=time.monotonic() - started,
            timed_out=False,
            exit_code=0,
        )


def resolve_adapter(
    name: str,
    command: str | None = None,
    script_path: Path | None = None,
    model: str = "command",
) -> AgentAdapter:
    """Resolve an adapter by name; unavailable adapters are reported, never faked."""
    if name == "command":
        if command is None:
            raise AdapterUnavailableError("the command adapter requires --agent-cmd")
        return CommandAdapter(command, model=model)
    if name == "scripted":
        if script_path is None:
            raise AdapterUnavailableError("the scripted adapter requires --script")
        return ScriptedAgentAdapter(load_fake_script(script_path))
    raise AdapterUnavailableError(
        f"adapter {name!r} is not available in this build; available adapters: command, scripted"
    )
