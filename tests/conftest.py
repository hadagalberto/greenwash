"""Shared fixtures and helpers for the harness test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from greenwash.fake_agent import FakeStep
from greenwash.models import Task
from greenwash.tasks import load_task

TASKS_DIR = Path(__file__).resolve().parents[1] / "tasks"


@pytest.fixture
def tasks_dir() -> Path:
    return TASKS_DIR


@pytest.fixture
def crc_task() -> Task:
    return load_task(TASKS_DIR / "crc32-check")


@pytest.fixture
def base64_task() -> Task:
    return load_task(TASKS_DIR / "base64url")


@pytest.fixture
def semver_task() -> Task:
    return load_task(TASKS_DIR / "semver-compare")


def write_step(path: str, content: str) -> FakeStep:
    """Build a scripted-agent write step."""
    return FakeStep(op="write", path=path, content=content)


def _encode(value: object) -> object:
    if isinstance(value, FakeStep):
        return {"op": value.op, "path": value.path, "content": value.content}
    raise TypeError(f"cannot encode {value!r} as script JSON")


def write_script(directory: Path, name: str, payload: dict[str, object]) -> Path:
    """Persist a scripted-agent payload so the CLI can load it."""
    path = directory / name
    path.write_text(json.dumps(payload, indent=2, default=_encode), encoding="utf-8")
    return path


def source_of(task: Task, overlay: str, relative: str) -> str:
    """Read a solution file from reference/, traps/ or mutants/."""
    return (task.root / overlay / relative).read_text(encoding="utf-8")
