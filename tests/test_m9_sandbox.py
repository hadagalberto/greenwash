"""Regression tests for milestone-9 sandbox findings 11, 17 and 19."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import write_fake_docker
from greenwash.sandbox import (
    DEFAULT_SANDBOX_IMAGE,
    DockerSandbox,
    LocalSandbox,
)


@pytest.mark.parametrize("mode", ["argv", "shell"])
def test_local_timeout_kills_descendant_processes(tmp_path: Path, mode: str) -> None:
    """Timeout must tear down the whole process tree, not just the direct child."""
    marker = tmp_path / "grandchild-alive.txt"
    child_code = (
        "import sys,time,pathlib;time.sleep(2);pathlib.Path(sys.argv[1]).write_text('alive')"
    )
    driver = tmp_path / "spawn.py"
    driver.write_text(
        "import subprocess,sys,time\n"
        f"child = {child_code!r}\n"
        f"marker = {str(marker)!r}\n"
        "subprocess.Popen([sys.executable, '-c', child, marker])\n"
        "time.sleep(5)\n",
        encoding="utf-8",
    )
    sandbox = LocalSandbox()
    started = time.monotonic()
    if mode == "argv":
        result = sandbox.run_argv([sys.executable, str(driver)], tmp_path, 1)
    else:
        result = sandbox.run_shell(f'"{sys.executable}" "{driver}"', tmp_path, 1)
    elapsed = time.monotonic() - started
    assert result.timed_out is True
    assert elapsed < 4, f"timeout not enforced (took {elapsed:.1f}s)"
    # Grandchild would write the marker ~2s after start if it survived.
    time.sleep(3)
    assert not marker.exists(), "grandchild process survived the timeout"


def test_local_sandbox_filters_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Secret host variables must not be inherited by agent subprocesses."""
    monkeypatch.setenv("GREENWASH_M9_SECRET", "do-not-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-leak-either")
    dump = tmp_path / "env.json"
    code = "import json,os,sys;json.dump(dict(os.environ),open(sys.argv[1],'w'))"
    result = LocalSandbox().run_argv(
        [sys.executable, "-c", code, str(dump)],
        tmp_path,
        10,
        env_extra={"GW_OPT_IN": "yes"},
    )
    assert result.returncode == 0, result.stderr
    child_env = json.loads(dump.read_text(encoding="utf-8"))
    assert "GREENWASH_M9_SECRET" not in child_env
    assert "OPENAI_API_KEY" not in child_env
    assert child_env.get("GW_OPT_IN") == "yes"
    assert child_env.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert any(key.upper() == "PATH" for key in child_env)


def test_run_argv_with_input_local(tmp_path: Path) -> None:
    result = LocalSandbox().run_argv_with_input(
        [sys.executable, "-c", "import sys;sys.stdout.write(sys.stdin.read().upper())"],
        tmp_path,
        10,
        "hello sandbox",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "HELLO SANDBOX"


def test_run_argv_with_input_docker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "docker.json"
    executable = write_fake_docker(tmp_path, log)
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
    result = DockerSandbox("unit:1", executable=str(executable)).run_argv_with_input(
        [sys.executable, "-c", "import sys;sys.stdout.write(sys.stdin.read().upper())"],
        tmp_path,
        10,
        "docker input",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "DOCKER INPUT"


def test_docker_prefix_uses_isolation_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "docker.json"
    executable = write_fake_docker(tmp_path, log)
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
    sandbox = DockerSandbox("unit:1", executable=str(executable))
    sandbox.run_shell("echo hi", tmp_path, 10)
    call = json.loads(log.read_text(encoding="utf-8"))[0]
    assert "--network" in call and "none" in call
    assert "--pids-limit" in call and "512" in call
    assert "--memory" in call and "2g" in call
    assert "--name" in call
    assert call[call.index("--name") + 1].startswith("greenwash-")
    if os.name == "nt":
        assert "--user" not in call
    else:
        getuid = getattr(os, "getuid", None)
        getgid = getattr(os, "getgid", None)
        assert getuid is not None and getgid is not None
        assert call[call.index("--user") + 1] == f"{getuid()}:{getgid()}"
    assert DEFAULT_SANDBOX_IMAGE == "greenwash-sandbox:latest"


def test_docker_timeout_kills_named_container(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        if "run" in argv:
            raise subprocess.TimeoutExpired(cmd=argv, timeout=1, output=b"", stderr=b"")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr("greenwash.sandbox.subprocess.run", fake_run)
    result = DockerSandbox("unit:1").run_shell("echo hi", tmp_path, 1)
    assert result.timed_out is True
    run_call = next(call for call in calls if "run" in call)
    kill_call = next(call for call in calls if "kill" in call)
    name = run_call[run_call.index("--name") + 1]
    assert kill_call[-1] == name
