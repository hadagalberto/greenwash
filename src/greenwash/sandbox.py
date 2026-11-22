"""Execution backends for agent processes and task test commands.

The default backend runs commands directly in the temporary workspace on the
host. The docker backend mounts that workspace at ``/work`` inside a container
and runs the same commands there; agents never receive host paths.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import shutil
import signal
import subprocess
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

CONTAINER_WORKDIR = "/work"
_DOCKER_TIMEOUT_GRACE_S = 10
_KILL_TIMEOUT_S = 5
_PIPE_DRAIN_TIMEOUT_S = 2
_DOCKER_KILL_TIMEOUT_S = 5
# Round-3 finding 4: a child that prints without end must not be able to grow
# the harness process. Keep the first and last MiB of each stream.
_OUTPUT_HEAD_BYTES = 1024 * 1024
_OUTPUT_TAIL_BYTES = 1024 * 1024
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


# Windows Job Object with KILL_ON_JOB_CLOSE. A process group is not enough:
# a grandchild started with DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP escapes
# it, but cannot escape a job that disallows BREAKAWAY_OK.
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


class _JobBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_ulong),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_ulong),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_ulong),
        ("SchedulingClass", ctypes.c_ulong),
    ]


class _JobIoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_ulonglong)
        for name in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )
    ]


class _JobExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobBasicLimitInformation),
        ("IoInfo", _JobIoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


_WIN_DLL = "WinDLL"  # indirect so POSIX type-checkers never see ctypes.WinDLL


def _kernel32() -> Any:
    return getattr(ctypes, _WIN_DLL)("kernel32", use_last_error=True)


def _create_job() -> int | None:
    """Create a kill-on-close job for the child, or None if unavailable."""
    if os.name != "nt":
        return None
    kernel32 = _kernel32()
    create = kernel32.CreateJobObjectW
    create.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    handle = create(None, None)
    if not handle:
        return None
    info = _JobExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    set_info = kernel32.SetInformationJobObject
    set_info.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
    set_info.restype = ctypes.c_int
    if not set_info(
        handle, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), ctypes.sizeof(info)
    ):
        _close_job(int(handle))
        return None
    return int(handle)


def _assign_job(job: int | None, proc: subprocess.Popen[bytes]) -> None:
    if job is None or os.name != "nt":
        return
    handle = getattr(proc, "_handle", None)
    if handle is None:
        return
    kernel32 = _kernel32()
    assign = kernel32.AssignProcessToJobObject
    assign.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    assign.restype = ctypes.c_int
    assign(job, int(handle))


def _close_job(job: int | None) -> None:
    """Closing the last job handle kills every process still inside it."""
    if job is None or os.name != "nt":
        return
    kernel32 = _kernel32()
    close = kernel32.CloseHandle
    close.argtypes = [ctypes.c_void_p]
    close.restype = ctypes.c_int
    close(job)


def _kill_process_tree(pid: int, pgid: int | None = None, job: int | None = None) -> None:
    """Best-effort kill of a process and every process it spawned."""
    if os.name == "nt":
        # taskkill /T walks the descendant tree; the job catches detached
        # grandchildren that are not descendants any more.
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=_KILL_TIMEOUT_S,
                check=False,
            )
        return
    # With start_new_session=True the child is its own group leader, so its
    # pgid equals its pid at spawn time. Calling getpgid(pid) after the leader
    # has exited fails and leaves the whole group running (finding 5).
    sigkill = getattr(signal, "SIGKILL", None)
    killpg = getattr(os, "killpg", None)
    if pgid is not None and sigkill is not None and killpg is not None:
        with contextlib.suppress(OSError):
            killpg(pgid, sigkill)


class _BoundedBuffer:
    """Keep a bounded head and tail of a byte stream.

    Reading a child's pipe into an unbounded ``communicate()`` buffer is how a
    looping printer grows the harness without limit. This buffer keeps at most
    ``_OUTPUT_HEAD_BYTES`` from the start and ``_OUTPUT_TAIL_BYTES`` from the
    end and reports when the cap was exceeded.
    """

    def __init__(self, head_limit: int, tail_limit: int) -> None:
        self._head_limit = head_limit
        self._tail_limit = tail_limit
        self._head = bytearray()
        self._tail = bytearray()
        self.total = 0
        self.exceeded = False

    def feed(self, chunk: bytes) -> bool:
        self.total += len(chunk)
        if len(self._head) < self._head_limit:
            take = min(len(chunk), self._head_limit - len(self._head))
            self._head.extend(chunk[:take])
            chunk = chunk[take:]
        if chunk:
            self._tail.extend(chunk)
            if len(self._tail) > self._tail_limit:
                del self._tail[: len(self._tail) - self._tail_limit]
        if self.total > self._head_limit + self._tail_limit:
            self.exceeded = True
        return self.exceeded

    def text(self) -> str:
        head = bytes(self._head).decode("utf-8", errors="replace")
        if not self._tail:
            return head
        tail = bytes(self._tail).decode("utf-8", errors="replace")
        return f"{head}\n... [output truncated] ...\n{tail}"


def _pump(pipe: Any, buffer: _BoundedBuffer, on_limit: Any) -> None:
    try:
        while True:
            chunk = pipe.read(65536)
            if not chunk:
                break
            if buffer.feed(chunk):
                on_limit()
    except (OSError, ValueError):
        pass
    finally:
        with contextlib.suppress(OSError):
            pipe.close()


def _run_process(
    argv_or_command: str | Sequence[str],
    shell: bool,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
    input_text: str | None = None,
    pass_fds: Sequence[int] = (),
) -> CommandOutput:
    """Run one command in its own process group, enforcing a hard deadline.

    ``subprocess.run(timeout=...)`` kills only the direct child; grandchildren
    that inherited the stdout/stderr pipes keep ``communicate()`` blocked.
    Round-3 findings 3 and 4 therefore replace ``communicate()`` with reader
    threads: wait for the leader first, kill its whole group as soon as it
    exits, and only then drain the pipes for a short deadline. Output is kept
    in bounded head/tail buffers and a child that exceeds the cap is killed.
    """
    new_session = os.name != "nt"
    try:
        proc = subprocess.Popen(
            argv_or_command,
            shell=shell,
            cwd=str(cwd),
            env=dict(env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if not new_session
            else 0,
            start_new_session=new_session,
            pass_fds=tuple(pass_fds) or (),
        )
    except OSError as exc:
        # A missing executable is a failed attempt, not a harness crash.
        return CommandOutput("", str(exc), 127, False)
    job = _create_job()
    _assign_job(job, proc)
    # start_new_session makes the child the leader of a new group before any
    # Python code runs, so the id is known without a later getpgid() call.
    pgid: int | None = proc.pid if new_session else None
    job_closed = False
    terminate_lock = threading.Lock()

    def terminate() -> None:
        nonlocal job_closed
        _kill_process_tree(proc.pid, pgid, job)
        with terminate_lock:
            if not job_closed:
                # Closing the job handle kills anything that survived taskkill,
                # such as a grandchild started with DETACHED_PROCESS (finding 5).
                _close_job(job)
                job_closed = True

    stdout_buffer = _BoundedBuffer(_OUTPUT_HEAD_BYTES, _OUTPUT_TAIL_BYTES)
    stderr_buffer = _BoundedBuffer(_OUTPUT_HEAD_BYTES, _OUTPUT_TAIL_BYTES)
    limit_hit = threading.Event()

    def on_limit() -> None:
        if not limit_hit.is_set():
            limit_hit.set()
            terminate()

    readers: list[threading.Thread] = []
    for pipe, buffer in ((proc.stdout, stdout_buffer), (proc.stderr, stderr_buffer)):
        if pipe is None:
            continue
        reader = threading.Thread(target=_pump, args=(pipe, buffer, on_limit), daemon=True)
        reader.start()
        readers.append(reader)

    stdin_writer: threading.Thread | None = None
    if input_text is not None and proc.stdin is not None:
        encoded = input_text.encode("utf-8")

        def write_stdin() -> None:
            assert proc.stdin is not None
            try:
                proc.stdin.write(encoded)
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass
            finally:
                with contextlib.suppress(OSError, ValueError):
                    proc.stdin.close()

        stdin_writer = threading.Thread(target=write_stdin, daemon=True)
        stdin_writer.start()
    elif proc.stdin is not None:
        with contextlib.suppress(OSError):
            proc.stdin.close()

    timed_out = False
    try:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=_KILL_TIMEOUT_S)
        # The leader is gone (or was killed): no descendant may keep running or
        # hold the pipes open.
        terminate()
        deadline = time.monotonic() + _PIPE_DRAIN_TIMEOUT_S
        for reader in readers:
            reader.join(max(0.0, deadline - time.monotonic()))
        if any(reader.is_alive() for reader in readers):
            terminate()
            for reader in readers:
                reader.join(0.5)
    finally:
        terminate()
        if stdin_writer is not None:
            stdin_writer.join(1)
        for pipe in (proc.stdout, proc.stderr):
            if pipe is not None:
                with contextlib.suppress(OSError):
                    pipe.close()
        if proc.returncode is None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=_KILL_TIMEOUT_S)

    stdout = stdout_buffer.text()
    stderr = stderr_buffer.text()
    returncode = proc.returncode if proc.returncode is not None else 1
    if timed_out:
        returncode = 1
    if limit_hit.is_set():
        returncode = 1
        stderr = (stderr + "\noutput limit exceeded").strip()
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
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput: ...

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput: ...

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
        env_extra: Mapping[str, str] | None = None,
        pass_fds: Sequence[int] = (),
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
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput:
        return _run_process(
            command, True, workdir, self._env(env_extra), timeout_s, pass_fds=pass_fds
        )

    def run_argv(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        env_extra: Mapping[str, str] | None = None,
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput:
        return _run_process(
            list(argv), False, workdir, self._env(env_extra), timeout_s, pass_fds=pass_fds
        )

    def run_argv_with_input(
        self,
        argv: Sequence[str],
        workdir: Path,
        timeout_s: int,
        input_text: str,
        env_extra: Mapping[str, str] | None = None,
        pass_fds: Sequence[int] = (),
    ) -> CommandOutput:
        return _run_process(
            list(argv),
            False,
            workdir,
            self._env(env_extra),
            timeout_s,
            input_text,
            pass_fds,
        )

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
        pass_fds: Sequence[int] = (),
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
        pass_fds: Sequence[int] = (),
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
        pass_fds: Sequence[int] = (),
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
