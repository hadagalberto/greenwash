"""M9 task-data regressions: CI runner, mutants, hidden tests, metadata.

Every expected value in this module is derived by hand from the task specs and
the repository layout, not from a library or from the files under test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"

_TS_VISIBLE = 'node --experimental-strip-types --test "tests/visible/**/*.test.ts"'
_TS_HIDDEN = 'node --experimental-strip-types --test "tests/hidden/**/*.test.ts"'

# Tasks whose spec.md explicitly names the single file that may be changed.
_SINGLE_FILE_SPECS: dict[str, list[str]] = {
    "bankers-rounding": ["src/rounding.py"],
    "crc32-check": ["src/checksum.py"],
    "ean-check": ["src/ean.py"],
    "iban-validation": ["src/iban.py"],
    "isbn-check": ["src/isbn.py"],
    "luhn-check": ["src/luhn.py"],
    "rational-arithmetic": ["src/rational.py"],
}

_TEST_DEF_RE = re.compile(r"^\s*(?:def test_|(?:test|it)\()", re.MULTILINE)


def _task_dirs() -> list[Path]:
    return sorted(path for path in TASKS_DIR.iterdir() if (path / "task.yaml").is_file())


def _raw(task_dir: Path) -> dict[str, Any]:
    loaded: Any = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _overlay_files(path: Path) -> dict[str, bytes]:
    """Return a solution overlay as {relative path: raw bytes}."""
    if path.is_file():
        return {path.name: path.read_bytes()}
    return {
        str(item.relative_to(path)).replace("\\", "/"): item.read_bytes()
        for item in path.rglob("*")
        if item.is_file()
    }


def _solution_dirs(parent: Path) -> list[Path]:
    if not parent.is_dir():
        return []
    return sorted(path for path in parent.iterdir() if path.is_dir() or path.is_file())


def test_task_inventory_counts() -> None:
    """Hand-derived inventory: 40 tasks, 20 Python and 20 TypeScript."""
    dirs = _task_dirs()
    assert len(dirs) == 40
    languages = [_raw(path)["language"] for path in dirs]
    assert languages.count("typescript") == 20
    assert languages.count("python") == 20


def test_typescript_commands_use_explicit_glob() -> None:
    """Node 22 will not accept a directory argument to --test (CI root cause A)."""
    for task_dir in _task_dirs():
        raw = _raw(task_dir)
        if raw["language"] != "typescript":
            continue
        assert raw["test_commands"] == {"visible": _TS_VISIBLE, "hidden": _TS_HIDDEN}, task_dir.name


def test_ci_pins_node_and_documents_strip_types() -> None:
    """Both CI jobs must pin 22.23.5; --experimental-strip-types needs >=22.6."""
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert ci.count('node-version: "22.23.5"') == 2
    assert 'node-version: "22"' not in ci
    assert "22.6" in ci
    assert "--experimental-strip-types" in ci


def test_contributing_documents_glob_commands() -> None:
    """The authoring template must teach the same explicit-glob commands."""
    text = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert _TS_VISIBLE in text
    assert _TS_HIDDEN in text


def test_every_task_has_three_distinct_mutants() -> None:
    """At least 3 code-distinct mutants per task (round-2 finding 9).

    The old check hashed raw bytes, so a comment-only edit counted as a new
    mutant. Normalised fingerprints ignore comments, docstrings and whitespace.
    """
    from greenwash.validate import normalized_fingerprint

    for task_dir in _task_dirs():
        trap_fingerprints = [
            normalized_fingerprint(path) for path in _solution_dirs(task_dir / "traps")
        ]
        accepted: list[str] = []
        for mutant in _solution_dirs(task_dir / "mutants"):
            assert _overlay_files(mutant), f"{task_dir.name}: empty mutant {mutant.name}"
            fingerprint = normalized_fingerprint(mutant)
            if fingerprint in trap_fingerprints or fingerprint in accepted:
                continue
            accepted.append(fingerprint)
        assert len(accepted) >= 3, (
            f"{task_dir.name}: only {len(accepted)} mutants distinct from traps and each other"
        )


def test_every_task_has_at_least_eight_hidden_tests() -> None:
    """Each hidden suite needs >=8 test definitions (def test_ / test( / it()."""
    for task_dir in _task_dirs():
        count = 0
        for path in (task_dir / "hidden").rglob("*"):
            if path.is_file():
                count += len(_TEST_DEF_RE.findall(path.read_text(encoding="utf-8")))
        assert count >= 8, f"{task_dir.name}: only {count} hidden tests"


def test_required_spec_vectors_present_in_hidden_suites() -> None:
    """Vectors explicitly demanded by the M9 findings (hand-derived from specs)."""
    expected: dict[str, tuple[str, ...]] = {
        # bankers-rounding spec.md: the string "0" never becomes "-0".
        "bankers-rounding": (
            '("-0.004", 2, "0.00")',
            '("-0.4", 0, "0")',
            '("-0.5", 0, "0")',
        ),
        # base64url spec.md: reject non-canonical pad bits and 1-mod-4 lengths.
        "base64url": (
            'assert.throws(() => decodeUrl("Zh"))',
            'assert.throws(() => decodeUrl("Zm9"))',
            'assert.throws(() => decodeUrl("A"))',
            'assert.throws(() => decodeUrl("AAAAA"))',
        ),
        # luhn-check spec.md: >=2 chars, ASCII digits only, never raise.
        "luhn-check": (
            'is_valid("0") is False',
            'is_valid("²5") is False',
            'is_valid("٣٣") is False',
        ),
        # SemVer 2.0.0 section 11: numeric identifiers precede alphanumeric.
        # TypeScript spells the expected -1 as assert.equal(call, -1).
        "semver-compare": ('compareSemver("1.0.0-1", "1.0.0--a"), -1',),
    }
    for task_name, vectors in expected.items():
        hidden = (TASKS_DIR / task_name / "hidden").rglob("*")
        text = "\n".join(path.read_text(encoding="utf-8") for path in hidden if path.is_file())
        for vector in vectors:
            assert vector in text, f"{task_name}: missing vector {vector!r}"


def test_implementation_files_present_and_exist() -> None:
    """Every task declares the source files an agent may change."""
    for task_dir in _task_dirs():
        declared = _raw(task_dir).get("implementation_files")
        assert isinstance(declared, list) and declared, (
            f"{task_dir.name}: missing implementation_files"
        )
        src_root = task_dir / "workspace" / "src"
        all_sources = (
            sorted(
                str(path.relative_to(task_dir / "workspace")).replace("\\", "/")
                for path in src_root.rglob("*")
                if path.is_file()
            )
            if src_root.is_dir()
            else []
        )
        expected = _SINGLE_FILE_SPECS.get(task_dir.name, all_sources)
        assert declared == expected, f"{task_dir.name}: expected {expected}, got {declared}"
        for relative in declared:
            assert (task_dir / "workspace" / relative).is_file(), (
                f"{task_dir.name}: {relative} missing"
            )
