"""Execution backends for agent processes and task test commands.

The default backend runs commands directly in the temporary workspace on the
host. The docker backend mounts that workspace at ``/work`` inside a container
and runs the same commands there; agents never receive host paths.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

CONTAINER_WORKDIR = "/work"
_DOCKER_TIMEOUT_GRACE_S = 10
_BASE_ENV: dict[str, str] = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPATH": CONTAINER_WORKDIR,
    "PYTHONUTF8": "1",
    "NO_COLOR": "1",
    "FORCE_COLOR": "0",
}


@dataclass(frozen=True)
class CommandOutput:
    """Normalised result of one sandboxed command."""

    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


@runtime_checkable
class Sandbox(Protocol):
    """Where agent and test commands execute."""

    @property
    def name(self) -> str: ...

    @property
    def native_python(self) -> bool:
        """Whether test commands should resolve ``python`` to this host's interpreter."""

    def run_shell(
        self,
        command: str,
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput: ...

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput: ...

    def translate_path(self, workdir: Path, path: Path) -> str:
        """Return the path as seen inside the sandbox."""

    def resolve_executable(self, executable: str) -> str:
        """Resolve a command name to something this sandbox can execute."""


class LocalSandbox:
    """Run commands on the host in ``workdir`` (the default)."""

    name = "local"
    native_python = True

    def _env(self, env_extra: Mapping[str, str] | None) -> dict[str, str]:
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        return env

    def run_shell(
        self,
        command: str,
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        stdout = stderr = ""
        returncode = 1
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(workdir),
                env=self._env(env_extra),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                check=False,
            )
            stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = _text(exc.stdout)
            stderr = _text(exc.stderr)
        return CommandOutput(stdout, stderr, returncode, timed_out)

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        stdout = stderr = ""
        returncode = 1
        timed_out = False
        try:
            completed = subprocess.run(
                list(argv),
                cwd=str(workdir),
                env=self._env(env_extra),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                check=False,
            )
            stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = _text(exc.stdout)
            stderr = _text(exc.stderr)
        return CommandOutput(stdout, stderr, returncode, timed_out)

    def translate_path(self, workdir: Path, path: Path) -> str:
        return str(path)

    def resolve_executable(self, executable: str) -> str:
        # Windows cannot spawn a bare .cmd/.bat name without a shell; a fully
        # qualified path works. On POSIX this is also the correct behaviour.
        return shutil.which(executable) or executable


class DockerSandbox:
    """Run commands inside a Docker container with the workspace mounted."""

    name = "docker"
    native_python = False

    def __init__(self, image: str, executable: str = "docker") -> None:
        image = image.strip()
        if not image:
            raise ValueError("--sandbox-image must not be empty")
        self.image = image
        # Resolve on the host: Windows may otherwise prefer a real docker.EXE
        # on PATH over a test double ending in .CMD.
        self.executable = shutil.which(executable) or executable

    def _env_args(self, env_extra: Mapping[str, str] | None) -> list[str]:
        env = dict(_BASE_ENV)
        if env_extra:
            env.update(env_extra)
        args: list[str] = []
        for key in sorted(env):
            args.extend(["-e", f"{key}={env[key]}"])
        return args

    def _prefix(self, workdir: Path, env_extra: Mapping[str, str] | None) -> list[str]:
        return [
            self.executable,
            "run",
            "--rm",
            "-v",
            f"{workdir}:{CONTAINER_WORKDIR}",
            "-w",
            CONTAINER_WORKDIR,
            *self._env_args(env_extra),
            self.image,
        ]

    def _execute(self, argv: list[str], timeout_s: int) -> CommandOutput:
        stdout = stderr = ""
        returncode = 1
        timed_out = False
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s + _DOCKER_TIMEOUT_GRACE_S,
                check=False,
            )
            stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = _text(exc.stdout)
            stderr = _text(exc.stderr)
            stderr += f"\nTIMEOUT after {timeout_s}s"
        return CommandOutput(stdout, stderr, returncode, timed_out)

    def run_shell(
        self,
        command: str,
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        argv = [*self._prefix(workdir, env_extra), "sh", "-c", command]
        return self._execute(argv, timeout_s)

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        return self._execute([*self._prefix(workdir, env_extra), *argv], timeout_s)

    def translate_path(self, workdir: Path, path: Path) -> str:
        try:
            relative = path.relative_to(workdir)
        except ValueError:
            return str(path)
        return f"{CONTAINER_WORKDIR}/{relative.as_posix()}"

    def resolve_executable(self, executable: str) -> str:
        # The name must be resolvable inside the image, not on the host.
        return executable


DEFAULT_SANDBOX_IMAGE = "python:3.12"


def build_sandbox(name: str, image: str = DEFAULT_SANDBOX_IMAGE) -> Sandbox:
    """Construct a sandbox by CLI name. Raises ``ValueError`` for unknown names."""
    if name == "local":
        return LocalSandbox()
    if name == "docker":
        return DockerSandbox(image)
    raise ValueError(f"unknown sandbox {name!r}; expected 'local' or 'docker'")
