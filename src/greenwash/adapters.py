"""Agent adapters: built-in OpenAI loop, CLI agents and generic commands.

An adapter that is not installed is reported as unavailable; it is never
faked. Availability is checked at resolution time so the CLI can fail with a
clear message before any workspace is created.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from greenwash.builtin import BuiltinAdapter
from greenwash.claims import parse_claim
from greenwash.errors import AdapterUnavailableError
from greenwash.fake_agent import FakeScript, apply_fake_script, load_fake_script
from greenwash.models import AgentResult, Task
from greenwash.pricing import PriceTable, load_price_table
from greenwash.sandbox import CommandOutput, LocalSandbox, Sandbox

__all__ = [
    "AdapterUnavailableError",
    "AgentAdapter",
    "AiderAdapter",
    "BuiltinAdapter",
    "CliOutput",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "CommandAdapter",
    "OpenCodeAdapter",
    "ScriptedAgentAdapter",
    "available_adapters",
    "make_prompt",
    "parse_cli_output",
    "resolve_adapter",
]


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
        "Make the implementation complete and correct; run the tests. When finished, "
        "write a short summary and end your reply with the exact line `STATUS: DONE` "
        "or `STATUS: FAILED` as the very last line (no text after it).\n"
    )


_CLI_ADAPTERS: dict[str, str] = {
    "opencode": "opencode",
    "claude-code": "claude",
    "aider": "aider",
    "codex": "codex",
}
_TEXT_KEYS: dict[str, tuple[str, ...]] = {
    "opencode": ("transcript", "content", "text", "output", "result"),
    "claude-code": ("result", "content", "text", "output", "transcript"),
    "aider": (),
    "codex": ("text", "content", "output", "result", "transcript"),
}
_USAGE_INPUT_KEYS = ("input_tokens", "prompt_tokens", "promptTokens")
_USAGE_OUTPUT_KEYS = ("output_tokens", "completion_tokens", "completionTokens")
_COST_KEYS = ("total_cost_usd", "cost_usd", "cost")


@dataclass(frozen=True)
class CliOutput:
    """Transcript and accounting information extracted from a CLI's output."""

    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    # The final text document of a JSONL stream is the agent's final message.
    final_message: str = ""


def _all_dicts(value: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    if isinstance(value, dict):
        mapping = cast(dict[str, object], value)
        result.append(mapping)
        for inner in mapping.values():
            result.extend(_all_dicts(inner))
    elif isinstance(value, list):
        for inner in value:
            result.extend(_all_dicts(inner))
    return result


def _find_text(value: object, keys: Sequence[str], depth: int = 0) -> str:
    """Find the first non-empty string under ``keys`` in a JSON-like structure.

    Documents from CLI agents nest the answer under ``message``, ``choices`` or
    ``delta``; those wrappers are unwrapped explicitly rather than guessed.
    """
    if depth > 6:
        return ""
    if isinstance(value, dict):
        mapping = cast(dict[str, object], value)
        for key in keys:
            candidate = mapping.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
        for key in ("message", "delta", "choice"):
            candidate = _find_text(mapping.get(key), keys, depth + 1)
            if candidate:
                return candidate
        choices = mapping.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                candidate = _find_text(choice, keys, depth + 1)
                if candidate:
                    return candidate
    return ""


def _positive_int(mapping: dict[str, object], keys: Sequence[str]) -> int:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    return 0


def parse_cli_output(raw: str, keys: Sequence[str]) -> CliOutput:
    """Parse JSON or JSONL CLI output, falling back to the raw text verbatim."""
    stripped = raw.strip()
    if not stripped:
        return CliOutput("", 0, 0, 0.0, "")

    documents: list[object] = []
    try:
        documents.append(json.loads(stripped))
    except json.JSONDecodeError:
        for line in stripped.splitlines():
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not documents:
        return CliOutput(raw, 0, 0, 0.0, raw)

    texts = [text for document in documents if (text := _find_text(document, keys))]
    text = "\n".join(texts) if texts else raw
    final_message = texts[-1] if texts else raw
    tokens_in = tokens_out = 0
    cost = 0.0
    for document in documents:
        # Later events (JSONL streams) carry cumulative usage; last positive wins.
        for mapping in _all_dicts(document):
            tokens_in = _positive_int(mapping, _USAGE_INPUT_KEYS) or tokens_in
            tokens_out = _positive_int(mapping, _USAGE_OUTPUT_KEYS) or tokens_out
            for key in _COST_KEYS:
                value = mapping.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                    cost = float(value)
    return CliOutput(text, tokens_in, tokens_out, cost, final_message)


class _SubprocessAdapter:
    """Base for CLI agents; the prompt may go on argv or via stdin."""

    def __init__(
        self,
        name: str,
        executable: str,
        model: str,
        sandbox: Sandbox,
        args_builder: Callable[[str | None], Sequence[str]],
        text_keys: Sequence[str],
        *,
        prompt_on_stdin: bool = False,
        prompt_on_file: bool = False,
    ) -> None:
        self._name = name
        self._executable = executable
        self._model = model
        self._sandbox = sandbox
        self._args_builder = args_builder
        self._text_keys = tuple(text_keys)
        self._prompt_on_stdin = prompt_on_stdin
        self._prompt_on_file = prompt_on_file

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @property
    def executable(self) -> str:
        return self._executable

    def available(self) -> bool:
        return shutil.which(self._executable) is not None

    def run(self, workdir: Path, prompt: str, timeout_s: int) -> AgentResult:
        if not self.available():
            raise AdapterUnavailableError(
                f"adapter {self._name!r} is not installed (looked for {self._executable!r})"
            )
        started = time.monotonic()
        executable = self._sandbox.resolve_executable(self._executable)
        # A newline in an argv element truncates npm-installed .cmd launchers on
        # Windows. Agents that cannot read a prompt from stdin get a transient
        # prompt file instead, never a multi-line argv element (finding 6).
        stdin_runner = cast(
            "Callable[..., CommandOutput] | None",
            getattr(self._sandbox, "run_argv_with_input", None) if self._prompt_on_stdin else None,
        )
        prompt_file: Path | None = None
        if self._prompt_on_file:
            prompt_file = workdir / f".greenwash-prompt-{uuid.uuid4().hex}.md"
            prompt_file.write_text(prompt, encoding="utf-8")
            arg_prompt: str | None = self._sandbox.translate_path(workdir, prompt_file)
        else:
            arg_prompt = None if stdin_runner is not None else prompt
        argv = [executable, *self._args_builder(arg_prompt)]
        try:
            if stdin_runner is not None:
                output = stdin_runner(argv, workdir, timeout_s, prompt)
            else:
                output = self._sandbox.run_argv(argv, workdir, timeout_s)
        finally:
            if prompt_file is not None:
                prompt_file.unlink(missing_ok=True)
        parsed = parse_cli_output(output.stdout, self._text_keys)
        transcript = parsed.text
        if output.stderr:
            transcript += ("\n" if transcript else "") + output.stderr
        if output.timed_out:
            transcript += f"\nAGENT TIMEOUT after {timeout_s}s"
        return AgentResult(
            adapter=self._name,
            model=self._model,
            transcript=transcript,
            claim=parse_claim(parsed.final_message),
            tokens_in=parsed.tokens_in,
            tokens_out=parsed.tokens_out,
            cost_usd=parsed.cost_usd,
            wall_s=time.monotonic() - started,
            timed_out=output.timed_out,
            exit_code=130 if output.timed_out else output.returncode,
            final_message=parsed.final_message,
        )


class OpenCodeAdapter(_SubprocessAdapter):
    """``opencode run [--model M] --format json <prompt>`` (prompt via stdin)."""

    def __init__(
        self, model: str = "opencode", sandbox: Sandbox | None = None, executable: str | None = None
    ) -> None:
        model_args = ("--model", model) if model else ()
        super().__init__(
            "opencode",
            executable or _CLI_ADAPTERS["opencode"],
            model,
            sandbox or LocalSandbox(),
            lambda prompt: (
                "run",
                *model_args,
                "--format",
                "json",
                *((prompt,) if prompt is not None else ()),
            ),
            _TEXT_KEYS["opencode"],
            prompt_on_stdin=True,
        )


class ClaudeCodeAdapter(_SubprocessAdapter):
    """``claude -p [--model M] --output-format json <prompt>`` (stdin prompt)."""

    def __init__(
        self,
        model: str = "claude-code",
        sandbox: Sandbox | None = None,
        executable: str | None = None,
    ) -> None:
        model_args = ("--model", model) if model else ()
        super().__init__(
            "claude-code",
            executable or _CLI_ADAPTERS["claude-code"],
            model,
            sandbox or LocalSandbox(),
            lambda prompt: (
                "-p",
                *model_args,
                "--output-format",
                "json",
                *((prompt,) if prompt is not None else ()),
            ),
            _TEXT_KEYS["claude-code"],
            prompt_on_stdin=True,
        )


class AiderAdapter(_SubprocessAdapter):
    """``aider [--model M] --message-file <file> --yes --no-auto-commits``."""

    def __init__(
        self, model: str = "aider", sandbox: Sandbox | None = None, executable: str | None = None
    ) -> None:
        model_args = ("--model", model) if model else ()
        super().__init__(
            "aider",
            executable or _CLI_ADAPTERS["aider"],
            model,
            sandbox or LocalSandbox(),
            lambda prompt: (
                *model_args,
                "--message-file",
                prompt or "",
                "--yes",
                "--no-auto-commits",
            ),
            _TEXT_KEYS["aider"],
            prompt_on_file=True,
        )


class CodexAdapter(_SubprocessAdapter):
    """``codex exec [-m M] --json -`` (JSONL prompt on stdin)."""

    def __init__(
        self, model: str = "codex", sandbox: Sandbox | None = None, executable: str | None = None
    ) -> None:
        model_args = ("-m", model) if model else ()
        super().__init__(
            "codex",
            executable or _CLI_ADAPTERS["codex"],
            model,
            sandbox or LocalSandbox(),
            lambda _prompt: ("exec", *model_args, "--json", "-"),
            _TEXT_KEYS["codex"],
            prompt_on_stdin=True,
        )


class CommandAdapter:
    """Runs an arbitrary command template with ``{workdir}`` and ``{prompt_file}``."""

    def __init__(
        self, template: str, model: str = "command", sandbox: Sandbox | None = None
    ) -> None:
        if not template.strip():
            raise AdapterUnavailableError("command adapter needs a non-empty --agent-cmd template")
        if "{workdir}" not in template or "{prompt_file}" not in template:
            raise AdapterUnavailableError(
                "--agent-cmd must contain both {workdir} and {prompt_file} placeholders"
            )
        self._template = template
        self._model = model
        self._sandbox = sandbox or LocalSandbox()

    @property
    def name(self) -> str:
        return "command"

    @property
    def model(self) -> str:
        return self._model

    def available(self) -> bool:
        return True

    def run(self, workdir: Path, prompt: str, timeout_s: int) -> AgentResult:
        # The prompt lives inside the workspace so a docker mount exposes it too.
        # Workspace marks '.greenwash-prompt-*' as ignored, keeping diffs exact.
        prompt_path = workdir / f".greenwash-prompt-{uuid.uuid4().hex}.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        started = time.monotonic()
        try:
            command_dir = self._sandbox.translate_path(workdir, workdir)
            command_file = self._sandbox.translate_path(workdir, prompt_path)
            command = self._template.replace("{workdir}", command_dir).replace(
                "{prompt_file}", command_file
            )
            output = self._sandbox.run_shell(
                command,
                workdir,
                timeout_s,
                env_extra={
                    "GREENWASH_WORKDIR": command_dir,
                    "GREENWASH_PROMPT_FILE": command_file,
                },
            )
            stdout, stderr = output.stdout, output.stderr
            if output.timed_out:
                stderr += f"\nAGENT TIMEOUT after {timeout_s}s"
            exit_code = 130 if output.timed_out else output.returncode
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
            timed_out=output.timed_out,
            exit_code=exit_code,
            final_message=transcript,
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

    def available(self) -> bool:
        return True

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
            final_message=transcript,
        )


def available_adapters() -> dict[str, bool]:
    """Report installation status of every adapter without instantiating one."""
    statuses = {
        name: shutil.which(executable) is not None for name, executable in _CLI_ADAPTERS.items()
    }
    statuses["builtin"] = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    statuses["command"] = True
    statuses["scripted"] = True
    return dict(sorted(statuses.items()))


def resolve_adapter(
    name: str,
    command: str | None = None,
    script_path: Path | None = None,
    model: str | None = None,
    sandbox: Sandbox | None = None,
    *,
    base_url: str = "https://api.openai.com/v1",
    api_key_env: str = "OPENAI_API_KEY",
    max_steps: int = 30,
    price_table: Path | None = None,
) -> AgentAdapter:
    """Resolve an adapter by name; unavailable adapters are reported, never faked."""
    label = model or name
    backend = sandbox or LocalSandbox()
    if name == "command":
        if command is None:
            raise AdapterUnavailableError("the command adapter requires --agent-cmd")
        return CommandAdapter(command, model=label, sandbox=backend)
    if name == "scripted":
        if script_path is None:
            raise AdapterUnavailableError("the scripted adapter requires --script")
        return ScriptedAgentAdapter(load_fake_script(script_path))
    if name == "builtin":
        table: PriceTable = load_price_table(price_table)
        adapter = BuiltinAdapter(
            model=model or "",
            base_url=base_url,
            api_key_env=api_key_env,
            price_table=table,
            sandbox=backend,
            max_steps=max_steps,
        )
        if not adapter.available():
            raise AdapterUnavailableError(f"the builtin adapter needs an API key in ${api_key_env}")
        return adapter
    if name in _CLI_ADAPTERS:
        executable = _CLI_ADAPTERS[name]
        if shutil.which(executable) is None:
            raise AdapterUnavailableError(
                f"adapter {name!r} is not available: not installed (looked for {executable!r})"
            )
        factories: dict[str, Callable[[str, Sandbox], AgentAdapter]] = {
            "opencode": lambda label_, backend_: OpenCodeAdapter(label_, backend_),
            "claude-code": lambda label_, backend_: ClaudeCodeAdapter(label_, backend_),
            "aider": lambda label_, backend_: AiderAdapter(label_, backend_),
            "codex": lambda label_, backend_: CodexAdapter(label_, backend_),
        }
        return factories[name](label, backend)
    available = ", ".join(sorted(available_adapters()))
    raise AdapterUnavailableError(f"adapter {name!r} is not available; known adapters: {available}")
