# Visible hunks start at line 1 and contain no context lines.
from src.hunk import parse_hunk_header
from src.patch import apply_patch


def test_simple_replacement() -> None:
    result = apply_patch(["a", "b", "c"], ["@@ -1,2 +1,2 @@", "-a", "-b", "+x", "+y"])
    assert result == ["x", "y", "c"]


def test_header_defaults() -> None:
    parsed = parse_hunk_header("@@ -1 +1 @@")
    assert (parsed.old_start, parsed.old_count, parsed.new_start, parsed.new_count) == (1, 1, 1, 1)


def test_bad_header_rejected() -> None:
    try:
        parse_hunk_header("not a header")
    except ValueError:
        return
    raise AssertionError("expected ValueError")
