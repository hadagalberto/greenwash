"""Tests for test-command execution and output parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from greenwash.commands import _command_tokens, run_tests
from greenwash.models import Language


def _make_pytest_suite(root: Path) -> None:
    tests = root / "tests"
    tests.mkdir(parents=True)
    (tests / "test_sample.py").write_text(
        "def test_ok_one():\n"
        "    assert 1 == 1\n\n"
        "def test_ok_two():\n"
        "    assert 2 == 2\n\n"
        "def test_bad():\n"
        "    assert 3 == 4\n",
        encoding="utf-8",
    )


def test_run_pytest_parses_pass_and_fail(tmp_path: Path) -> None:
    _make_pytest_suite(tmp_path)
    outcome = run_tests("python -m pytest -q tests", tmp_path, 30, Language.PYTHON)
    assert (outcome.passed, outcome.failed, outcome.total) == (2, 1, 3)
    assert outcome.ok is False
    assert outcome.timed_out is False
    assert outcome.returncode != 0
    assert outcome.score == pytest.approx(2 / 3)


def test_run_pytest_parses_all_passing(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    outcome = run_tests("python -m pytest -q tests", tmp_path, 30, Language.PYTHON)
    assert outcome.ok is True
    assert (outcome.passed, outcome.failed, outcome.total) == (1, 0, 1)
    assert outcome.score == 1.0


def test_run_node_parses_summary(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "sample.test.ts").write_text(
        "import { test } from 'node:test';\n"
        "import assert from 'node:assert/strict';\n"
        "test('ok', () => assert.equal(1, 1));\n"
        "test('bad', () => assert.equal(2, 3));\n",
        encoding="utf-8",
    )
    outcome = run_tests(
        "node --experimental-strip-types --test tests", tmp_path, 30, Language.TYPESCRIPT
    )
    assert (outcome.passed, outcome.failed, outcome.total) == (1, 1, 2)
    assert outcome.ok is False


def test_run_tests_enforces_timeout(tmp_path: Path) -> None:
    outcome = run_tests('python -c "import time; time.sleep(5)"', tmp_path, 1, Language.PYTHON)
    assert outcome.timed_out is True
    assert outcome.failed >= 1
    assert "TIMEOUT" in outcome.stderr


def test_command_tokens_resolves_python_and_rejects_empty() -> None:
    import sys

    assert _command_tokens("python -m pytest")[0] == sys.executable
    with pytest.raises(ValueError, match="empty test command"):
        _command_tokens("   ")
