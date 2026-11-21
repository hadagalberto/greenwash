# SPEC RULE MAP (round-2 finding 8): normative spec sentence -> hidden test(s).
# Every rule below is exercised by at least one test in this directory.
# R1: Starts must be `>= 1`, counts `>= 0`.
#     -> test_bad_ranges, test_context_and_shifted_start, test_context_mismatch_is_rejected
# R2: Their lengths must equal `old_count` and `new_count` from the ...
#     -> test_count_mismatch_is_rejected, test_default_count_is_one, test_bad_ranges
# R3: The old sequence at that position must match exactly, or ...
#     -> test_bad_ranges, test_context_and_shifted_start, test_context_mismatch_is_rejected
#
# Hand-built hunks with context, shifted starts and mismatch detection.
import pytest
from src.hunk import parse_hunk_header
from src.patch import apply_patch


def test_context_and_shifted_start() -> None:
    patch = ["--- old", "+++ new", "@@ -2,3 +2,4 @@", " b", "-c", "+C", "+X", " d"]
    assert apply_patch(["a", "b", "c", "d"], patch) == ["a", "b", "C", "X", "d"]


def test_no_newline_marker_is_ignored() -> None:
    patch = ["@@ -1,1 +1,1 @@", "-a", "+A", "\\ No newline at end of file"]
    assert apply_patch(["a"], patch) == ["A"]


def test_no_newline_marker_mid_hunk_is_ignored() -> None:
    # SPEC.md: "A line `\ No newline at end of file` is ignored anywhere in a hunk."
    patch = ["@@ -1,1 +1,1 @@", "-a", "\\ No newline at end of file", "+A"]
    assert apply_patch(["a"], patch) == ["A"]


def test_default_count_is_one() -> None:
    parsed = parse_hunk_header("@@ -3 +4 @@ trailing context")
    assert (parsed.old_start, parsed.old_count, parsed.new_start, parsed.new_count) == (3, 1, 4, 1)


def test_multiple_hunks_use_updated_positions() -> None:
    patch = ["@@ -1,1 +1,2 @@", "-a", "+A", "+A2", "@@ -4,1 +4,1 @@", "-c", "+C"]
    assert apply_patch(["a", "b", "c"], patch) == ["A", "A2", "b", "C"]


def test_context_mismatch_is_rejected() -> None:
    patch = ["@@ -2,2 +2,2 @@", " wrong", "-c", "+C"]
    with pytest.raises(ValueError):
        apply_patch(["a", "b", "c"], patch)


def test_count_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError):
        apply_patch(["a", "b"], ["@@ -1,2 +1,2 @@", "-a", "-b", "+x"])


def test_hunk_outside_document_is_rejected() -> None:
    with pytest.raises(ValueError):
        apply_patch(["a"], ["@@ -5,1 +5,1 @@", "-a", "+b"])


@pytest.mark.parametrize("bad", ["@@ -0,1 +1,1 @@", "@@ -1,-1 +1,1 @@", "@@ -1 + @@"])
def test_bad_ranges(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_hunk_header(bad)
