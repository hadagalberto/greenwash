"""Deterministic scripted agent used by the harness test suite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from greenwash.models import ClaimStatus

Operation = Literal["write", "delete", "append"]


@dataclass(frozen=True)
class FakeStep:
    """One filesystem operation replayed by the scripted agent."""

    op: Operation
    path: str
    content: str = ""


@dataclass(frozen=True)
class FakeScript:
    """A complete scripted agent run."""

    steps: tuple[FakeStep, ...]
    status: ClaimStatus
    summary: str


class FakeScriptError(ValueError):
    """Raised when a scripted-agent JSON file is malformed."""


def load_fake_script(path: Path) -> FakeScript:
    """Load and validate a scripted-agent JSON file."""
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FakeScriptError(f"cannot read fake-agent script {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise FakeScriptError("fake-agent script must be a JSON object")
    mapping = cast(dict[str, object], raw)
    steps_raw = mapping.get("steps")
    if not isinstance(steps_raw, list):
        raise FakeScriptError("fake-agent script needs a steps array")

    steps: list[FakeStep] = []
    for index, item in enumerate(steps_raw):
        if not isinstance(item, dict):
            raise FakeScriptError(f"steps[{index}] must be an object")
        step = cast(dict[str, object], item)
        op = step.get("op")
        target = step.get("path")
        content = step.get("content", "")
        if op not in {"write", "delete", "append"}:
            raise FakeScriptError(f"steps[{index}].op must be write, delete or append")
        if not isinstance(target, str) or not target:
            raise FakeScriptError(f"steps[{index}].path must be a non-empty string")
        if not isinstance(content, str):
            raise FakeScriptError(f"steps[{index}].content must be a string")
        steps.append(FakeStep(op=op, path=target, content=content))

    status_raw = mapping.get("status", "DONE")
    if not isinstance(status_raw, str) or status_raw not in {"DONE", "FAILED", "UNKNOWN"}:
        raise FakeScriptError("status must be DONE, FAILED or UNKNOWN")
    summary = mapping.get("summary", "")
    if not isinstance(summary, str):
        raise FakeScriptError("summary must be a string")
    return FakeScript(
        steps=tuple(steps),
        status=ClaimStatus(status_raw),
        summary=summary,
    )


def _safe_path(workdir: Path, relative: str) -> Path:
    parts = Path(relative).parts
    if ".." in parts or Path(relative).is_absolute():
        raise FakeScriptError(f"script path escapes the workspace: {relative}")
    return workdir / relative


def apply_fake_script(script: FakeScript, workdir: Path) -> str:
    """Apply a script to a workspace and return a realistic transcript."""
    lines: list[str] = ["greenwash scripted agent starting"]
    for step in script.steps:
        target = _safe_path(workdir, step.path)
        if step.op == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(step.content, encoding="utf-8")
        elif step.op == "append":
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(step.content)
        elif step.op == "delete" and target.exists():
            target.unlink()
        lines.append(f"applied {step.op} to {step.path}")
    lines.append("ran tests")
    if script.summary:
        lines.append(script.summary)
    lines.append(f"STATUS: {str(script.status)}")
    return "\n".join(lines) + "\n"
