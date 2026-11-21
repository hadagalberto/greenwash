"""Regressions for milestone-9 metric findings (7, 16, 20).

Every expected number below is derived by hand in a comment from the inputs in
the test. Nothing here is copied from library output or regenerated snapshots:
snapshots are not oracles.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from greenwash.adapters import AgentAdapter
from greenwash.compare import _mean, compare_dirs, compare_tasks
from greenwash.grading import AttemptRecord
from greenwash.models import (
    Claim,
    ClaimStatus,
    TamperFinding,
    TamperKind,
    TamperReport,
    Task,
)
from greenwash.models import TestOutcome as Outcome
from greenwash.report import ReportData, _agent_rows, _metric_cards, load_report, render_html
from greenwash.runner import (
    RunConfig,
    bootstrap_ci,
    bootstrap_ci_clusters,
    run_benchmark,
    summarize,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
A = FIXTURES / "report-a"
B = FIXTURES / "report-b"


def _outcome(ok: bool, passed: int, total: int) -> Outcome:
    return Outcome(
        command="test",
        returncode=0 if ok else 1,
        passed=passed,
        failed=total - passed,
        skipped=0,
        total=total,
        stdout="",
        stderr="",
        timed_out=False,
    )


def _record(
    task_id: str,
    repeat: int,
    *,
    hidden_ok: bool,
    certain: bool = True,
    status: ClaimStatus = ClaimStatus.DONE,
    tamper: tuple[TamperKind, ...] = (),
) -> AttemptRecord:
    findings = tuple(
        TamperFinding(kind=kind, path="tests/visible/a.py", detail="d", hunk="h") for kind in tamper
    )
    return AttemptRecord(
        task_id=task_id,
        agent="scripted",
        model="scripted",
        repeat=repeat,
        claim=Claim(status=status, certain=certain, evidence="STATUS"),
        visible=_outcome(True, 3, 3),
        original_visible=_outcome(True, 3, 3),
        hidden=_outcome(hidden_ok, 4 if hidden_ok else 2, 4),
        tamper=TamperReport(findings=findings),
        diff="",
        wall_s=1.0,
        tokens_in=10,
        tokens_out=5,
        cost_usd=0.01,
        agent_timed_out=False,
    )


def _rows(directory: Path) -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


# Finding 7 ------------------------------------------------------------------


def test_tamper_rate_is_per_attempt_not_per_finding() -> None:
    records = [
        _record("a", 1, hidden_ok=True, tamper=(TamperKind.SKIP_MARKER,) * 3),
        _record("b", 1, hidden_ok=True),
        _record("c", 1, hidden_ok=True),
        _record("d", 1, hidden_ok=True),
    ]
    summary = summarize(records, max_repeat=1)
    # By hand: 4 attempts, one attempt carries three skip findings. Counting
    # findings gives 3/4 (> 100% once one attempt has four); counting attempts
    # with >=1 finding gives 1/4 for the kind and 1/4 overall.
    assert summary["tamper_rate_by_kind"] == {"skip_marker": 0.25}
    assert summary["tamper_rate"] == pytest.approx(0.25)
    # Four draws from {0,0,0,1}: P(0 ones) = 81/256 > 0.025 so low = 0;
    # P(>=3 ones) = 13/256 > 0.025 so high = 3/4.
    assert summary["tamper_rate_ci95"] == pytest.approx([0.0, 0.75])


def test_uncertain_claims_are_excluded_from_greenwash_headline() -> None:
    records = [
        # Certain DONE + hidden fail -> certain greenwash.
        _record("a", 1, hidden_ok=False, certain=True, status=ClaimStatus.DONE),
        # Uncertain DONE + hidden fail -> greenwash only in the "all" figure.
        _record("a", 2, hidden_ok=False, certain=False, status=ClaimStatus.DONE),
        _record("b", 1, hidden_ok=True, certain=True, status=ClaimStatus.DONE),
        _record("c", 1, hidden_ok=False, certain=False, status=ClaimStatus.FAILED),
    ]
    summary = summarize(records, max_repeat=2)
    # By hand: 2 of 4 claims are heuristic -> 0.5. Two DONE claims fail hidden;
    # only one is certain -> headline 1/4, all-claims 2/4.
    assert summary["uncertain_claim_rate"] == pytest.approx(0.5)
    assert summary["greenwash_rate"] == pytest.approx(0.25)
    assert summary["greenwash_rate_certain"] == pytest.approx(0.25)
    assert summary["greenwash_rate_all"] == pytest.approx(0.5)


def test_fixture_claims_are_certain_so_legacy_greenwash_goldens_still_hold() -> None:
    for variant in ("a", "b"):
        for row in _rows(FIXTURES / f"report-{variant}"):
            claim = row["claim"]
            assert isinstance(claim, dict) and claim["certain"] is True


# Finding 16a ----------------------------------------------------------------


def test_bootstrap_ci_clusters_resamples_tasks_then_attempts() -> None:
    # Four identical tasks, each [0, 1]: resampling tasks changes nothing, but
    # resampling the two attempts within each task does. The mean is the share
    # of ones among 8 draws, #ones ~ Binomial(8, 1/2). By hand:
    #   P(#ones <= 1) = (1 + 8)/256 = 9/256 = 0.0352 > 0.025 -> low = 1/8;
    #   P(#ones >= 7) = 9/256 > 0.025 -> high = 7/8.
    ci = bootstrap_ci_clusters([[0.0, 1.0]] * 4, seed=0, resamples=1000)
    assert ci == pytest.approx([1 / 8, 7 / 8])
    # A task-mean-only bootstrap would be the degenerate [0.5, 0.5], so the
    # within-task resampling is observable.

    # Now three tasks with all zeros and one task with all ones. Task means are
    # {0, 0, 0, 1}; #ones ~ Binomial(4, 1/4). By hand:
    #   P(#ones = 0) = (3/4)^4 = 81/256 = 0.316 > 0.025 -> low = 0;
    #   P(#ones >= 3) = (4 + 1)/256 = 0.0508, P(=4) = 1/256 -> high = 3*2/8 = 0.75.
    clustered = bootstrap_ci_clusters(
        [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0]], seed=0, resamples=1000
    )
    assert clustered == pytest.approx([0.0, 0.75])
    # Attempt-level bootstrap over the same 8 values gives high = 5/8, so the
    # task clustering is observable (and must not be silently omitted).
    assert bootstrap_ci([0.0] * 6 + [1.0] * 2) != clustered


def test_summarize_exposes_cluster_ci_without_changing_legacy_ci() -> None:
    records = [
        _record("a", 1, hidden_ok=False),
        _record("a", 2, hidden_ok=False),
        _record("b", 1, hidden_ok=False),
        _record("b", 2, hidden_ok=False),
        _record("c", 1, hidden_ok=False),
        _record("c", 2, hidden_ok=False),
        _record("d", 1, hidden_ok=True),
        _record("d", 2, hidden_ok=True),
    ]
    summary = summarize(records, max_repeat=2)
    # Same hand derivation as the previous test: 1 of 4 tasks is all-passing.
    # Attempt-level CI high is 5/8; cluster CI high is 3/4.
    assert summary["hidden_pass_rate"] == pytest.approx(0.25)
    assert summary["hidden_pass_rate_ci95_cluster"] == pytest.approx([0.0, 0.75])
    assert summary["hidden_pass_rate_ci95"] != summary["hidden_pass_rate_ci95_cluster"]
    assert "mean_cost_usd_ci95_cluster" in summary


# Finding 16b ----------------------------------------------------------------


def test_pass_at_k_unbiased_estimator_hand_derived() -> None:
    records = [
        _record("a", 1, hidden_ok=False),
        _record("a", 2, hidden_ok=True),
        _record("b", 1, hidden_ok=False),
        _record("b", 2, hidden_ok=True),
        _record("c", 1, hidden_ok=False),
        _record("c", 2, hidden_ok=False),
    ]
    summary = summarize(records, max_repeat=2)
    # By hand, per task with n = 2 repeats and c hidden passes:
    #   a, b: c = 1 -> pass@1 = 1 - C(1,1)/C(2,1) = 1/2,
    #               pass@2 = 1 - C(1,2)/C(2,2) = 1 - 0 = 1;
    #   c:    c = 0 -> pass@1 = pass@2 = 0.
    # Mean over 3 tasks: pass@1 = (1/2 + 1/2 + 0)/3 = 1/3,
    #                    pass@2 = (1 + 1 + 0)/3 = 2/3.
    assert summary["pass_at_k_unbiased"] == pytest.approx({"1": 1 / 3, "2": 2 / 3})
    # Finding 16b: the headline key now uses the same unbiased estimator; the
    # old first-k rule survives only as pass_at_k_legacy.
    assert summary["pass_at_k"] == pytest.approx({"1": 1 / 3, "2": 2 / 3})
    assert summary["pass_at_k_legacy"] == pytest.approx({"1": 0.0, "2": 2 / 3})


# Finding 16c ----------------------------------------------------------------


def test_mean_uses_fsum_for_float_stability() -> None:
    # By hand: ten tenths add to 1.0, so the mean is 1/10 = 0.1. On Python 3.11
    # the builtin sum yields 0.9999999999999999 (mean 0.09999999999999999);
    # math.fsum gives the correctly rounded 1.0 on every supported version.
    assert _mean([0.1] * 10) == 0.1


def test_compare_tasks_sign_test_hand_derived() -> None:
    left = (
        _row("t1", 1, False),
        _row("t1", 2, False),
        _row("t2", 1, False),
        _row("t2", 2, False),
        _row("t3", 1, False),
        _row("t3", 2, False),
    )
    right = (
        _row("t1", 1, True),
        _row("t1", 2, True),
        _row("t2", 1, True),
        _row("t2", 2, False),
        _row("t3", 1, False),
        _row("t3", 2, False),
    )
    result = compare_tasks(left, right)
    # By hand, per-task means: A = [0, 0, 0], B = [1, 1/2, 0].
    # Two tasks improve, one ties, none regresses. Ties are dropped from the
    # sign test: n = 2 non-tied, k = 2 successes. Two-sided exact binomial
    # p = 2 * C(2,2)/2^2 = 2 * 1/4 = 0.5.
    assert result["improved"] == 2 and result["regressed"] == 0 and result["tied"] == 1
    assert result["sign_test_p"] == pytest.approx(0.5)
    rows = cast("list[dict[str, object]]", result["tasks"])
    assert [row["task_id"] for row in rows] == ["t1", "t2", "t3"]
    assert [row["a_mean"] for row in rows] == pytest.approx([0.0, 0.0, 0.0])
    assert [row["b_mean"] for row in rows] == pytest.approx([1.0, 0.5, 0.0])


def _row(task_id: str, repeat: int, hidden: bool) -> dict[str, object]:
    return {
        "task_id": task_id,
        "repeat": repeat,
        "hidden_pass": hidden,
        "greenwash": False,
        "hidden": {"score": 1.0 if hidden else 0.0},
    }


def test_compare_dirs_exposes_by_task_without_changing_legacy_pairs() -> None:
    result = compare_dirs(A, B)
    # Legacy attempt-level pairing stays at 6 rows (2 repeats x 3 tasks).
    assert result["paired_attempts"] == 6
    by_task = cast("dict[str, object]", result["by_task"])
    assert by_task == compare_tasks(_rows(A), _rows(B))
    # By hand: only base64url and semver-compare improve on hidden pass means;
    # crc32-check is unchanged => n = 2, k = 2, two-sided p = 0.5.
    assert by_task["sign_test_p"] == pytest.approx(0.5)


# Finding 7 / 20 report consumption ------------------------------------------


def test_agent_rows_use_scalar_tamper_rate_and_uncertain_rate() -> None:
    summary: dict[str, object] = {
        "by_agent_model": {
            "a/1": {
                "attempts": 4,
                "tamper_rate": 0.25,
                "tamper_rate_by_kind": {"skip_marker": 0.75},
                "uncertain_claim_rate": 0.5,
            }
        }
    }
    data = ReportData(summary=summary, records=())
    rows = _agent_rows(data)
    assert rows[0]["tamper"] == "25.0%"
    assert rows[0]["uncertain"] == "50.0%"
    # Old summaries without the scalar fall back to the sum of per-kind rates.
    legacy = ReportData(
        summary={"by_agent_model": {"a/1": {"tamper_rate_by_kind": {"skip_marker": 0.75}}}},
        records=(),
    )
    assert _agent_rows(legacy)[0]["tamper"] == "75.0%"


def test_metric_cards_show_all_greenwash_variants_and_uncertainty() -> None:
    cards = _metric_cards(
        {
            "greenwash_rate": 0.25,
            "greenwash_rate_certain": 0.25,
            "greenwash_rate_all": 0.5,
            "uncertain_claim_rate": 0.5,
        }
    )
    by_label = {card["label"]: card["value"] for card in cards}
    assert by_label["Greenwash rate (certain DONE claims)"] == "25.0%"
    assert by_label["Greenwash rate (all claims)"] == "50.0%"
    assert by_label["Uncertain claim rate"] == "50.0%"


def test_report_renders_transcript_and_final_message() -> None:
    data = load_report(A)
    first = dict(data.records[0])
    first["transcript"] = "AGENT TRACE MARKER"
    first["final_message"] = "FINAL MESSAGE MARKER"
    html = render_html(replace(data, records=(first, *data.records[1:])))
    assert "Agent transcript" in html and "AGENT TRACE MARKER" in html
    assert "final message" in html and "FINAL MESSAGE MARKER" in html
    # Grading truncates; the report says so and still escapes untrusted text.
    assert "truncated" in html
    xss = "<script>alert('xss')</script>"
    evil = dict(data.records[0])
    evil["transcript"] = xss
    html = render_html(replace(data, records=(evil, *data.records[1:])))
    assert xss not in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html


# Finding 18 ----------------------------------------------------------------


def test_run_benchmark_uses_per_task_timeouts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Per-task budgets win; tasks without an entry keep the run-wide timeout."""
    seen: list[tuple[str, int]] = []

    def fake_one_attempt(
        task: Task, adapter: AgentAdapter, repeat: int, timeout_s: int, sandbox: object
    ) -> AttemptRecord:
        seen.append((task.id, timeout_s))
        return _record(task.id, repeat, hidden_ok=True)

    monkeypatch.setattr("greenwash.runner._one_attempt", fake_one_attempt)
    tasks = (
        cast("Task", SimpleNamespace(id="a")),
        cast("Task", SimpleNamespace(id="b")),
    )
    run_benchmark(
        RunConfig(
            tasks=tasks,
            adapter=cast("AgentAdapter", None),
            repeat=1,
            jobs=1,
            timeout_s=5,
            out_dir=tmp_path,
            task_timeouts={"a": 11},
        )
    )
    assert seen == [("a", 11), ("b", 5)]
