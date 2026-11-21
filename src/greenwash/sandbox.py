"""Execution backends for agent processes and task test commands.

The default backend runs commands directly in the temporary workspace on the
host. The docker backend mounts that workspace at ``/work`` inside a container
and runs the same commands there; agents never receive host paths.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

CONTAINER_WORKDIR = "/work"
_DOCKER_TIMEOUT_GRACE_S = 10
_KILL_TIMEOUT_S = 5
_PIPE_DRAIN_TIMEOUT_S = 2
_DOCKER_KILL_TIMEOUT_S = 5
_BASE_ENV: dict[str, str] = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPATH": CONTAINER_WORKDIR,
    "PYTHONUTF8": "1",
    "NO_COLOR": "1",
    "FORCE_COLOR": "0",
}
_LOCAL_BASE_ENV: dict[str, str] = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
    "NO_COLOR": "1",
    "FORCE_COLOR": "0",
}
# Only these host variables (plus PYTHON* settings) are forwarded to agents.
# Never forward credentials such as OPENAI_API_KEY into a sandboxed process.
_ALLOWED_ENV_KEYS = frozenset(
    {
        "PATH",
        "HOME",
        "USERPROFILE",
        "TEMP",
        "TMP",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "SYSTEMROOT",
        "PATHEXT",
        "COMSPEC",
        "APPDATA",
        "LOCALAPPDATA",
    }
)


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


def _kill_process_tree(pid: int) -> None:
    """Best-effort kill of a process and every process it spawned."""
    if os.name == "nt":
        # taskkill /T walks the descendant tree; a new process group alone is
        # not enough on Windows because grandchildren inherit it.
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=_KILL_TIMEOUT_S,
                check=False,
            )
        return
    # getattr keeps the POSIX-only symbols portable under Windows type checkers.
    killpg = getattr(os, "killpg", None)
    getpgid = getattr(os, "getpgid", None)
    sigkill = getattr(signal, "SIGKILL", None)
    if killpg is not None and getpgid is not None and sigkill is not None:
        with contextlib.suppress(OSError):
            killpg(getpgid(pid), sigkill)


def _run_process(
    argv_or_command: str | Sequence[str],
    shell: bool,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
    input_text: str | None = None,
) -> CommandOutput:
    """Run one command in its own process group, enforcing a hard deadline.

    ``subprocess.run(timeout=...)`` kills only the direct child; grandchildren
    that inherited the stdout/stderr pipes keep ``communicate()`` blocked.
    Killing the whole group (tree on Windows) before draining the pipes makes
    the timeout real instead of best-effort.
    """
    try:
        proc = subprocess.Popen(
            argv_or_command,
            shell=shell,
            cwd=str(cwd),
            env=dict(env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
    except OSError as exc:
        # A missing executable is a failed attempt, not a harness crash.
        return CommandOutput("", str(exc), 127, False)

    stdout: str = ""
    stderr: str = ""
    timed_out = False
    try:
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _text(exc.stdout)
        stderr = _text(exc.stderr)
        _kill_process_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=_PIPE_DRAIN_TIMEOUT_S)
        except subprocess.TimeoutExpired as second:
            # Last resort: kill again and keep whatever bytes we already have.
            _kill_process_tree(proc.pid)
            stdout = stdout or _text(second.stdout)
            stderr = stderr or _text(second.stderr)
    finally:
        # No process (or descendant holding a pipe) may outlive a run.
        _kill_process_tree(proc.pid)
        if proc.stdout is not None:
            proc.stdout.close()
        if proc.stderr is not None:
            proc.stderr.close()
    returncode = proc.returncode if proc.returncode is not None else 1
    if timed_out:
        returncode = 1
    return CommandOutput(stdout, stderr, returncode, timed_out)


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

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
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
        env: dict[str, str] = {}
        for key, value in os.environ.items():
            upper = key.upper()
            if upper in _ALLOWED_ENV_KEYS or upper.startswith("PYTHON"):
                env[key] = value
        env.update(_LOCAL_BASE_ENV)
        # Explicit opt-ins always win, including secrets a caller needs.
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
        return _run_process(command, True, workdir, self._env(env_extra), timeout_s)

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        return _run_process(list(argv), False, workdir, self._env(env_extra), timeout_s)

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        return _run_process(list(argv), False, workdir, self._env(env_extra), timeout_s, input_text)

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

    def _prefix(
        self,
        workdir: Path,
        env_extra: Mapping[str, str] | None,
        name: str,
        interactive: bool = False,
    ) -> list[str]:
        args = [
            self.executable,
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            "none",
            "--pids-limit",
            "512",
            "--memory",
            "2g",
        ]
        if os.name != "nt":
            getuid = getattr(os, "getuid", None)
            getgid = getattr(os, "getgid", None)
            if getuid is not None and getgid is not None:
                args.extend(["--user", f"{getuid()}:{getgid()}"])
        if interactive:
            args.append("-i")
        args.extend(
            [
                "-v",
                f"{workdir}:{CONTAINER_WORKDIR}",
                "-w",
                CONTAINER_WORKDIR,
                *self._env_args(env_extra),
                self.image,
            ]
        )
        return args

    def _kill_container(self, name: str) -> None:
        """Kill the named container on timeout; failures are not fatal."""
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                [self.executable, "kill", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=_DOCKER_KILL_TIMEOUT_S,
                check=False,
            )

    def _execute(
        self,
        argv: list[str],
        timeout_s: int,
        name: str,
        input_text: str | None = None,
    ) -> CommandOutput:
        stdout = stderr = ""
        returncode = 1
        timed_out = False
        try:
            if input_text is None:
                completed = subprocess.run(
                    argv,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_s + _DOCKER_TIMEOUT_GRACE_S,
                    check=False,
                )
            else:
                completed = subprocess.run(
                    argv,
                    input=input_text,
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
            self._kill_container(name)
        except OSError as exc:
            # A missing docker binary must fail the attempt, not abort the run.
            returncode = 127
            stderr = str(exc)
        return CommandOutput(stdout, stderr, returncode, timed_out)

    def run_shell(
        self,
        command: str,
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        name = f"greenwash-{uuid.uuid4().hex}"
        argv = [*self._prefix(workdir, env_extra, name), "sh", "-c", command]
        return self._execute(argv, timeout_s, name)

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        name = f"greenwash-{uuid.uuid4().hex}"
        return self._execute([*self._prefix(workdir, env_extra, name), *argv], timeout_s, name)

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
        env_extra: Mapping[str, str] | None = None,
    ) -> CommandOutput:
        name = f"greenwash-{uuid.uuid4().hex}"
        prefix = self._prefix(workdir, env_extra, name, interactive=True)
        return self._execute([*prefix, *argv], timeout_s, name, input_text)

    def translate_path(self, workdir: Path, path: Path) -> str:
        try:
            relative = path.relative_to(workdir)
        except ValueError:
            return str(path)
        return f"{CONTAINER_WORKDIR}/{relative.as_posix()}"

    def resolve_executable(self, executable: str) -> str:
        # The name must be resolvable inside the image, not on the host.
        return executable


DEFAULT_SANDBOX_IMAGE = "greenwash-sandbox:latest"


def build_sandbox(name: str, image: str = DEFAULT_SANDBOX_IMAGE) -> Sandbox:
    """Construct a sandbox by CLI name. Raises ``ValueError`` for unknown names."""
    if name == "local":
        return LocalSandbox()
    if name == "docker":
        return DockerSandbox(image)
    raise ValueError(f"unknown sandbox {name!r}; expected 'local' or 'docker'")
