"""Tests for local and docker command execution backends."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import write_fake_docker
from greenwash.sandbox import (
    CONTAINER_WORKDIR,
    DockerSandbox,
    LocalSandbox,
    build_sandbox,
)


def test_local_sandbox_runs_shell_and_argv(tmp_path: Path) -> None:
    sandbox = LocalSandbox()
    assert sandbox.name == "local"
    assert sandbox.native_python is True
    shell = sandbox.run_shell(f'{sys.executable} -c "print(6*7)"', tmp_path, 10)
    assert shell.stdout.strip() == "42"
    assert shell.returncode == 0
    argv = sandbox.run_argv([sys.executable, "-c", "import sys; sys.exit(3)"], tmp_path, 10)
    assert argv.returncode == 3
    assert sandbox.translate_path(tmp_path, tmp_path / "a.txt") == str(tmp_path / "a.txt")


def test_local_sandbox_reports_timeout(tmp_path: Path) -> None:
    result = LocalSandbox().run_shell(
        f'{sys.executable} -c "import time; time.sleep(1)"', tmp_path, 0
    )
    assert result.timed_out is True
    assert result.returncode == 1


def test_docker_sandbox_wraps_commands_and_mounts_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "docker-calls.json"
    executable = write_fake_docker(tmp_path, log)
    monkeypatch.setenv("FAKE_DOCKER_LOG", str(log))
    monkeypatch.setenv("FAKE_DOCKER_IMAGE", "unit:1")
    sandbox = DockerSandbox("unit:1", executable=str(executable))
    work = tmp_path / "work"
    work.mkdir()
    (work / "hello.txt").write_text("hi", encoding="utf-8")
    shell = sandbox.run_shell(
        f'{sys.executable} -c "print(7*6)"',
        work,
        10,
        env_extra={"GREENWASH_TEST": "yes"},
    )
    argv_result = sandbox.run_argv([sys.executable, "-c", "print('argv ok')"], work, 10)

    assert shell.stdout.strip() == "42"
    assert argv_result.stdout.strip() == "argv ok"
    calls = json.loads(log.read_text(encoding="utf-8"))
    assert len(calls) == 2
    first = calls[0]
    assert first[:2] == ["run", "--rm"]
    assert f"{work}:{CONTAINER_WORKDIR}" in first
    assert "-w" in first and CONTAINER_WORKDIR in first
    assert "-e" in first and "GREENWASH_TEST=yes" in first
    assert "unit:1" in first
    assert first[-3:] == ["sh", "-c", f'{sys.executable} -c "print(7*6)"']
    assert calls[1][-3:] == [sys.executable, "-c", "print('argv ok')"]
    assert sandbox.translate_path(work, work / "hello.txt") == f"{CONTAINER_WORKDIR}/hello.txt"
    assert sandbox.translate_path(work, tmp_path / "outside.txt") == str(tmp_path / "outside.txt")
    assert sandbox.name == "docker" and sandbox.native_python is False


def test_docker_sandbox_reports_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            cmd="docker run",
            timeout=5,
            output=b"partial out",
            stderr=b"partial err",
        )

    monkeypatch.setattr("greenwash.sandbox.subprocess.run", explode)
    result = DockerSandbox("unit:1").run_shell("echo hi", tmp_path, 5)
    assert result.timed_out is True
    assert "partial out" in result.stdout
    assert "partial err" in result.stderr and "TIMEOUT after 5s" in result.stderr
    assert result.returncode == 1


def test_build_sandbox_selection() -> None:
    assert isinstance(build_sandbox("local"), LocalSandbox)
    docker = build_sandbox("docker", "unit:2")
    assert isinstance(docker, DockerSandbox) and docker.image == "unit:2"
    with pytest.raises(ValueError, match="unknown sandbox"):
        build_sandbox("podman")
    with pytest.raises(ValueError, match="must not be empty"):
        DockerSandbox("  ")
