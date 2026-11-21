"""Regression tests for defects found in the milestone-8 audit.

Each case is derived from SPEC.md or from a hostile-input probe in ``.review/``:
the behaviours below were confirmed broken before the corresponding fix.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from greenwash.cli import main
from greenwash.models import TamperKind
from greenwash.pricing import PriceTableError, parse_price_table
from greenwash.report import ReportData, load_report, render_html
from greenwash.tamper import analyze_diff


def _rename(old: str, new: str) -> str:
    """A pure git rename: a header with no hunk body."""
    return (
        f"diff --git a/{old} b/{new}\nsimilarity index 100%\nrename from {old}\nrename to {new}\n"
    )


# --- tamper: test files moved out of the graded suite -----------------------


def test_rename_out_of_visible_suite_is_a_deleted_test() -> None:
    """A rename into another directory removes the test from the visible suite."""
    report = analyze_diff(_rename("tests/visible/test_a.py", "tests/disabled/test_a.py"))
    assert report.by_kind().get(str(TamperKind.DELETED_TEST)) == 1


def test_rename_out_of_test_tree_is_a_deleted_test() -> None:
    """The old rule missed a move when the new filename still looked like a test."""
    report = analyze_diff(_rename("tests/visible/test_a.py", "src/test_a.py"))
    assert report.by_kind().get(str(TamperKind.DELETED_TEST)) == 1


def test_rename_to_uncollected_name_is_a_deleted_test() -> None:
    """`test_a.py` -> `a.py` is no longer collected by pytest's test_*.py rule."""
    report = analyze_diff(_rename("tests/visible/test_a.py", "tests/visible/a.py"))
    assert report.by_kind().get(str(TamperKind.DELETED_TEST)) == 1


def test_rename_between_test_names_in_same_dir_is_not_a_deletion() -> None:
    """A purely renamed test file in the same directory is still graded."""
    report = analyze_diff(_rename("tests/visible/test_a.py", "tests/visible/test_b.py"))
    assert str(TamperKind.DELETED_TEST) not in report.by_kind()


def test_removed_line_starting_with_double_dash_is_analysed() -> None:
    """`---` is a file header only before a hunk; inside a hunk it is content."""
    diff = (
        "diff --git a/tests/visible/test_a.py b/tests/visible/test_a.py\n"
        "--- a/tests/visible/test_a.py\n"
        "+++ b/tests/visible/test_a.py\n"
        "@@ -1,1 +1,0 @@\n"
        "---assert f() == 1\n"
    )
    report = analyze_diff(diff)
    assert report.by_kind().get(str(TamperKind.ASSERTION_REMOVED)) == 1


# --- hostile numeric inputs -------------------------------------------------


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_price_table_rejects_non_finite_numbers(token: str) -> None:
    """Non-finite prices would emit invalid JSON from summary.json."""
    raw = json.loads(
        '{"version": 1, "source": "unit", "models": {"m": {"input": ' + token + ', "output": 0}}}'
    )
    with pytest.raises(PriceTableError, match="finite"):
        parse_price_table(raw)


# --- CLI argument validation ------------------------------------------------


@pytest.mark.parametrize("timeout", ["0", "-1"])
def test_cli_rejects_non_positive_timeout(timeout: str, capsys: pytest.CaptureFixture[str]) -> None:
    """A zero/negative timeout makes every subprocess time out immediately."""
    # A glob matching nothing keeps this test about argument validation, not
    # about running the 40-task oracle suite.
    assert (
        main(["validate-tasks", "--tasks", "tasks", "--glob", "no-such-task", "--timeout", timeout])
        == 2
    )
    assert "--timeout" in capsys.readouterr().out
    assert (
        main(
            [
                "run",
                "--agent",
                "scripted",
                "--tasks",
                "tasks",
                "--glob",
                "no-such-task",
                "--timeout",
                timeout,
            ]
        )
        == 2
    )
    assert "--timeout" in capsys.readouterr().out


# --- output path validation -------------------------------------------------


@pytest.mark.parametrize("command", ["run", "compare"])
def test_cli_rejects_out_path_that_is_a_file(
    command: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file at --out must be a clean usage error, not an uncaught OSError."""
    out_file = tmp_path / "out"
    out_file.write_text("not a directory\n", encoding="utf-8")
    if command == "run":
        argv = [
            "run",
            "--agent",
            "scripted",
            "--script",
            "examples/honest-crc32.json",
            "--tasks",
            "tasks",
            "--glob",
            "crc32-check",
            "--out",
            str(out_file),
        ]
    else:
        argv = [
            "compare",
            "tests/fixtures/report-a",
            "tests/fixtures/report-b",
            "--out",
            str(out_file),
        ]
    assert main(argv) == 2
    assert "--out" in capsys.readouterr().out


# --- malformed result files -------------------------------------------------


def test_report_rejects_non_standard_json_constants(tmp_path: Path) -> None:
    """NaN/Infinity in a result file must be a clear ReportError, not nan% output."""
    summary = (Path("tests/fixtures/report-a") / "summary.json").read_text(encoding="utf-8")
    (tmp_path / "summary.json").write_text(summary, encoding="utf-8")
    (tmp_path / "results.jsonl").write_text(
        '{"task_id": "t", "agent": "a", "model": "m", "cost_usd": NaN}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        load_report(tmp_path)


# --- report determinism -----------------------------------------------------


def test_pass_at_k_is_sorted_numerically() -> None:
    """k=10 must not be rendered before k=2 because of string sorting."""
    data = ReportData(
        summary={
            "tasks": ["t"],
            "overall": {
                "attempts": 1,
                "pass_at_k": {"10": 0.1, "2": 0.2, "1": 0.3},
                "tamper_rate_by_kind": {},
            },
            "by_agent_model": {},
        },
        records=(),
    )
    html = render_html(data)
    assert html.index("pass@1 ") < html.index("pass@2 ") < html.index("pass@10 ")
