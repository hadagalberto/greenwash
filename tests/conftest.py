"""Shared fixtures and helpers for the harness test suite."""

from __future__ import annotations

import json
import os
import sys
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


def install_fake_exe(directory: Path, name: str, python_script: Path) -> Path:
    """Create a platform-appropriate launcher for a fake CLI executable."""
    if os.name == "nt":
        launcher = directory / f"{name}.cmd"
        launcher.write_text(f'@"{sys.executable}" "{python_script}" %*\n', encoding="utf-8")
    else:
        launcher = directory / name
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{python_script}" "$@"\n', encoding="utf-8"
        )
        launcher.chmod(0o755)
    return launcher


def write_fake_cli(
    directory: Path,
    name: str,
    stdout: str,
    *,
    stderr: str = "",
    exit_code: int = 0,
    log_env: str = "FAKE_CLI_LOG",
) -> Path:
    """Install a fake CLI that prints fixed output and records its argv (no network)."""
    script = directory / f"{name}_impl.py"
    script.write_text(
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"record = Path(os.environ[{log_env!r}])\n"
        "record.write_text(\n"
        "            json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}), encoding='utf-8'\n"
        "        )\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.stderr.write({stderr!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    return install_fake_exe(directory, name, script)


def write_fake_docker(directory: Path, log_path: Path) -> Path:
    """Install a fake `docker` that records argv and emulates `docker run` locally."""
    script = directory / "fake_docker_impl.py"
    script.write_text(
        "import json\n"
        "import os\n"
        "import shutil\n"
        "import subprocess\n"
        "import sys\n"
        "from pathlib import Path\n"
        "argv = sys.argv[1:]\n"
        "log = Path(os.environ['FAKE_DOCKER_LOG'])\n"
        "calls = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []\n"
        "calls.append(argv)\n"
        "log.write_text(json.dumps(calls), encoding='utf-8')\n"
        "workdir = ''\n"
        "for i, arg in enumerate(argv):\n"
        "    if arg == '-v' and i + 1 < len(argv):\n"
        "        workdir = argv[i + 1].rsplit(':', 1)[0]\n"
        "image = os.environ['FAKE_DOCKER_IMAGE']\n"
        "command = argv[argv.index(image) + 1:] if image in argv else []\n"
        "if command[:2] == ['sh', '-c']:\n"
        "    inner = command[2].replace('/work', workdir)\n"
        "    completed = subprocess.run(inner, shell=True, cwd=workdir or None,\n"
        "                               capture_output=True, text=True)\n"
        "else:\n"
        "    local_argv = [arg.replace('/work', workdir) for arg in command]\n"
        "    if local_argv:\n"
        "        local_argv[0] = shutil.which(local_argv[0]) or local_argv[0]\n"
        "    completed = subprocess.run(local_argv, cwd=workdir or None,\n"
        "                               capture_output=True, text=True)\n"
        "sys.stdout.write(completed.stdout)\n"
        "sys.stderr.write(completed.stderr)\n"
        "sys.exit(completed.returncode)\n",
        encoding="utf-8",
    )
    return install_fake_exe(directory, "docker", script)
