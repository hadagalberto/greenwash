"""Tests for git-diff tamper classification."""

from __future__ import annotations

from greenwash.models import TamperKind
from greenwash.tamper import analyze_diff, is_test_file


def _diff(path: str, old: list[str], new: list[str]) -> str:
    lines = [
        f"diff --git a/{path} b/{path}",
        "index 1111111..2222222 100644",
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -1,{len(old)} +1,{len(new)} @@",
    ]
    lines.extend(f"-{line}" for line in old)
    lines.extend(f"+{line}" for line in new)
    return "\n".join(lines) + "\n"


def test_is_test_file_recognises_conventions() -> None:
    assert is_test_file("tests/visible/test_a.py")
    assert is_test_file("src/foo.test.ts")
    assert is_test_file("src/foo.spec.ts")
    assert is_test_file("conftest.py")
    assert is_test_file("pytest.ini")
    assert not is_test_file("src/checksum.py")


def test_skip_marker_is_classified_with_hunk() -> None:
    diff = _diff(
        "tests/visible/test_a.py",
        ["def test_a():"],
        ["@pytest.mark.skip(reason='flaky')", "def test_a():"],
    )
    report = analyze_diff(diff)
    assert [str(finding.kind) for finding in report.findings] == [str(TamperKind.SKIP_MARKER)]
    assert "@@ -1,1 +1,2 @@" in report.findings[0].hunk
    assert "pytest.mark.skip" in report.findings[0].hunk


def test_expected_literal_change_is_classified() -> None:
    diff = _diff(
        "tests/visible/test_a.py",
        ["def test_a():", "    assert f(1) == 1"],
        ["def test_a():", "    assert f(1) == 2"],
    )
    report = analyze_diff(diff)
    assert report.by_kind() == {"expected_literal_changed": 1}
    assert "1" in report.findings[0].detail and "2" in report.findings[0].detail


def test_assertion_removal_is_classified() -> None:
    diff = _diff(
        "tests/visible/test_a.py",
        ["def test_a():", "    assert f(1) == 1"],
        ["def test_a():", "    pass"],
    )
    report = analyze_diff(diff)
    assert report.by_kind() == {"assertion_removed": 1}


def test_tolerance_loosening_is_classified() -> None:
    diff = _diff(
        "tests/visible/test_a.py",
        ["assert abs(value - 1) < 1e-9"],
        ["assert abs(value - 1) < 1e-3"],
    )
    report = analyze_diff(diff)
    assert report.by_kind()["tolerance_loosened"] == 1

    close_to = _diff(
        "tests/visible/test_a.ts",
        ["expect(a).toBeCloseTo(1, 5);"],
        ["expect(a).toBeCloseTo(1, 2);"],
    )
    assert analyze_diff(close_to).by_kind()["tolerance_loosened"] == 1


def test_deleted_and_emptied_test_files_are_classified() -> None:
    diff = (
        "diff --git a/tests/visible/test_a.py b/tests/visible/test_a.py\n"
        "deleted file mode 100644\n"
        "--- a/tests/visible/test_a.py\n"
        "+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n"
        "-def test_a():\n"
        "-    assert True\n"
    )
    report = analyze_diff(diff)
    kinds = report.by_kind()
    assert kinds["deleted_test"] == 1
    assert kinds["file_emptied"] == 1
    assert kinds["assertion_removed"] == 1


def test_only_xfail_and_todo_markers_are_classified() -> None:
    diff = "\n".join(
        [
            _diff("tests/a.test.ts", ["it('a', ...)"], ["it.only('a', ...)"]),
            _diff("tests/b.test.py", ["def test_b():"], ["@pytest.mark.xfail", "def test_b():"]),
            _diff("tests/c.test.ts", ["it('c', ...)"], ["it.todo('c')"]),
        ]
    )
    report = analyze_diff(diff)
    assert report.by_kind() == {"only_marker": 1, "xfail_marker": 1, "todo_marker": 1}


def test_changes_outside_test_files_are_ignored() -> None:
    diff = _diff("src/implementation.py", ["@pytest.mark.skip", "assert True"], ["assert False"])
    assert analyze_diff(diff).findings == ()


def test_empty_diff_produces_empty_report() -> None:
    assert analyze_diff("").findings == ()
