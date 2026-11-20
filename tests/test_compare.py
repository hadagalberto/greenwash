"""Golden tests for paired comparison of two result directories."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from greenwash.cli import main
from greenwash.compare import CompareError, compare_dirs, pair_records

FIXTURES = Path(__file__).resolve().parent / "fixtures"
A = FIXTURES / "report-a"
B = FIXTURES / "report-b"


def _rows(directory: Path) -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def test_golden_compare_json_matches_fixtures() -> None:
    payload = compare_dirs(A, B)
    golden = (FIXTURES / "golden" / "compare.json").read_text(encoding="utf-8")
    assert json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n" == golden


def test_exact_paired_metrics_on_fixture_results() -> None:
    result = compare_dirs(A, B)
    assert result["paired_attempts"] == 6
    assert result["tasks"] == ["base64url", "crc32-check", "semver-compare"]
    assert result["unpaired_a"] == [] and result["unpaired_b"] == []
    assert result["outcomes"] == {"b_better": 2, "b_worse": 0, "tie": 4}

    a = result["a"]
    b = result["b"]
    assert isinstance(a, dict) and isinstance(b, dict)
    assert a["hidden_pass_rate"] == pytest.approx(1 / 3)
    assert b["hidden_pass_rate"] == pytest.approx(2 / 3)
    assert a["greenwash_rate"] == pytest.approx(1 / 2)
    assert b["greenwash_rate"] == pytest.approx(1 / 3)
    assert a["partial_hidden_score"] == pytest.approx(0.625)
    assert b["partial_hidden_score"] == pytest.approx(0.625 + 1 / 6)
    assert a["visible_pass_rate"] == pytest.approx(5 / 6)
    assert b["visible_pass_rate"] == 1.0
    assert a["tamper_findings_per_attempt"] == b["tamper_findings_per_attempt"] == 1 / 3

    delta = result["delta"]
    assert isinstance(delta, dict)
    hidden = delta["hidden_pass_rate"]
    assert isinstance(hidden, dict)
    assert hidden["mean"] == pytest.approx(1 / 3)
    assert hidden["ci95"] == pytest.approx([0.0, 2 / 3])
    greenwash = delta["greenwash_rate"]
    assert isinstance(greenwash, dict)
    assert greenwash["mean"] == pytest.approx(-1 / 6)
    assert greenwash["ci95"] == pytest.approx([-0.5, 0.0])
    partial = delta["partial_hidden_score"]
    assert isinstance(partial, dict)
    assert partial["mean"] == pytest.approx(1 / 6)
    assert partial["ci95"] == pytest.approx([0.0, 1 / 3])


def test_pair_rows_have_known_valid_and_invalid_vectors() -> None:
    pairs = compare_dirs(A, B)["pairs"]
    assert isinstance(pairs, list)
    by_key = {(row["task_id"], row["repeat"]): row for row in pairs}
    assert len(by_key) == 6
    fixed = by_key[("base64url", 1)]
    assert fixed["a_hidden_pass"] is False and fixed["b_hidden_pass"] is True
    assert fixed["a_greenwash"] is True and fixed["b_greenwash"] is False
    assert fixed["hidden_pass_delta"] == 1.0
    assert fixed["greenwash_delta"] == -1.0
    unchanged_greenwash = by_key[("base64url", 2)]
    assert unchanged_greenwash["a_greenwash"] is True
    assert unchanged_greenwash["b_greenwash"] is True
    assert unchanged_greenwash["hidden_pass_delta"] == 0.0
    honest_failure = by_key[("semver-compare", 2)]
    assert honest_failure["a_hidden_pass"] is False
    assert honest_failure["a_greenwash"] is False


def test_unpaired_attempts_are_reported_not_silently_dropped() -> None:
    left = _rows(A)
    right = _rows(B)[:-1]
    result = pair_records(left, right)
    assert result["paired_attempts"] == 5
    # The candidate directory is missing this attempt, so it is unpaired on the A side.
    assert result["unpaired_a"] == ["semver-compare#2"]
    assert result["unpaired_b"] == []


def test_duplicate_key_is_rejected() -> None:
    rows = _rows(A)
    with pytest.raises(CompareError, match="duplicate attempt"):
        pair_records(rows, (rows[0], rows[0]))


def test_bad_repeat_and_missing_task_are_rejected() -> None:
    rows = _rows(A)
    bad = dict(rows[0])
    bad["repeat"] = 0
    with pytest.raises(CompareError, match="repeat must be a positive integer"):
        pair_records((bad,), rows[:1])
    missing = dict(rows[0])
    del missing["task_id"]
    with pytest.raises(CompareError, match="missing task_id"):
        pair_records((missing,), rows[:1])


def test_compare_dirs_reports_missing_results() -> None:
    with pytest.raises(CompareError, match="missing result file"):
        compare_dirs(Path("/does/not/exist"), B)
    with pytest.raises(CompareError, match="missing result file"):
        compare_dirs(A, Path("/does/not/exist"))


def test_cli_compare_prints_json_and_writes_compare_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "comparison"
    assert main(["compare", str(A), str(B), "--out", str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == compare_dirs(A, B)
    assert (out / "compare.json").is_file()
    assert (out / "compare.json").read_text(encoding="utf-8") == (
        FIXTURES / "golden" / "compare.json"
    ).read_text(encoding="utf-8")


def test_cli_compare_rejects_missing_directory(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compare", str(Path("/does/not/exist")), str(B)]) == 2
    assert "error:" in capsys.readouterr().out
