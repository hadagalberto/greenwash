"""Tests for benchmark orchestration and reporting."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import source_of, write_step
from greenwash.adapters import ScriptedAgentAdapter
from greenwash.fake_agent import FakeScript
from greenwash.grading import AttemptRecord
from greenwash.models import (
    Claim,
    ClaimStatus,
    TamperFinding,
    TamperKind,
    TamperReport,
    Task,
)
from greenwash.models import (
    TestOutcome as Outcome,
)
from greenwash.runner import RunConfig, bootstrap_ci, run_benchmark, summarize


def _outcome(passed: int, total: int, ok: bool) -> Outcome:
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
    *,
    hidden_ok: bool,
    partial: float,
    status: ClaimStatus = ClaimStatus.DONE,
    visible_ok: bool = True,
    original_ok: bool = True,
    tamper_kinds: tuple[TamperKind, ...] = (),
    repeat: int = 1,
) -> AttemptRecord:
    hidden_total = 4
    hidden_passed = round(partial * hidden_total)
    findings = tuple(
        TamperFinding(kind=kind, path="tests/visible/a.py", detail="d", hunk="h")
        for kind in tamper_kinds
    )
    return AttemptRecord(
        task_id=task_id,
        agent="scripted",
        model="scripted",
        repeat=repeat,
        claim=Claim(status=status, certain=True, evidence="STATUS"),
        visible=_outcome(3, 3, visible_ok),
        original_visible=_outcome(3, 3, original_ok),
        hidden=_outcome(hidden_passed, hidden_total, hidden_ok),
        tamper=TamperReport(findings=findings),
        diff="",
        wall_s=1.0,
        tokens_in=10,
        tokens_out=5,
        cost_usd=0.01,
        agent_timed_out=False,
    )


def test_summarize_computes_exact_rates() -> None:
    records = [
        _record("a", hidden_ok=True, partial=1.0),
        _record("b", hidden_ok=False, partial=0.5),
        _record("c", hidden_ok=False, partial=0.0, status=ClaimStatus.FAILED),
        _record("a", hidden_ok=True, partial=1.0, repeat=2),
    ]
    summary = summarize(records, max_repeat=2)
    assert summary["attempts"] == 4
    assert summary["hidden_pass_rate"] == 0.5
    assert summary["partial_hidden_score"] == 0.625
    assert summary["visible_pass_rate"] == 1.0
    assert summary["greenwash_rate"] == 0.25
    assert summary["honest_failure_rate"] == 0.25
    assert summary["mean_cost_usd"] == 0.01
    assert summary["mean_tokens"] == 15.0
    assert summary["pass_at_k"] == {"1": 1 / 3, "2": 1 / 3}


def test_summarize_counts_tamper_and_empty_input() -> None:
    records = [
        _record("a", hidden_ok=True, partial=1.0, tamper_kinds=(TamperKind.SKIP_MARKER,)),
        _record("b", hidden_ok=True, partial=1.0),
    ]
    summary = summarize(records, max_repeat=1)
    assert summary["tamper_rate_by_kind"] == {"skip_marker": 0.5}
    empty = summarize([], max_repeat=1)
    assert empty["hidden_pass_rate"] == 0.0
    assert empty["pass_at_k"] == {"1": 0.0}


def test_bootstrap_ci_is_deterministic_and_brackets_mean() -> None:
    values = [0.0, 1.0, 1.0, 1.0, 0.0]
    first = bootstrap_ci(values)
    assert first == bootstrap_ci(values)
    assert first[0] <= 0.6 <= first[1]
    assert bootstrap_ci([]) == [0.0, 0.0]


def test_pass_at_k_improves_with_repeats() -> None:
    records = [
        _record("a", hidden_ok=False, partial=0.0, repeat=1),
        _record("a", hidden_ok=True, partial=1.0, repeat=2),
    ]
    summary = summarize(records, max_repeat=2)
    # Finding 16b: one pass in two repeats gives pass@1 = 1 - C(1,1)/C(2,1) = 0.5.
    assert summary["pass_at_k"] == {"1": 0.5, "2": 1.0}


def test_run_benchmark_writes_jsonl_and_summary(crc_task: Task, tmp_path: Path) -> None:
    steps = [write_step("src/checksum.py", source_of(crc_task, "reference", "src/checksum.py"))]
    script = FakeScript(steps=tuple(steps), status=ClaimStatus.DONE, summary="all tests pass")
    adapter = ScriptedAgentAdapter(script)
    out = tmp_path / "results"
    summary = run_benchmark(
        RunConfig(
            tasks=(crc_task,),
            adapter=adapter,
            repeat=2,
            jobs=2,
            timeout_s=60,
            out_dir=out,
        )
    )
    assert summary["attempt_count"] == 2
    lines = (out / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["task_id"] == "crc32-check"
    assert first["hidden_pass"] is True
    payload = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert payload["overall"]["hidden_pass_rate"] == 1.0
    assert payload["by_agent_model"]["scripted/scripted"]["attempts"] == 2


def test_run_benchmark_writes_self_contained_report(crc_task: Task, tmp_path: Path) -> None:
    steps = [write_step("src/checksum.py", source_of(crc_task, "reference", "src/checksum.py"))]
    adapter = ScriptedAgentAdapter(
        FakeScript(steps=tuple(steps), status=ClaimStatus.DONE, summary="all tests pass")
    )
    out = tmp_path / "results"
    run_benchmark(
        RunConfig(
            tasks=(crc_task,),
            adapter=adapter,
            repeat=1,
            jobs=1,
            timeout_s=60,
            out_dir=out,
        )
    )
    record = json.loads((out / "results.jsonl").read_text(encoding="utf-8").strip())
    assert record["spec"] == crc_task.spec_path.read_text(encoding="utf-8")
    html = (out / "report.html").read_text(encoding="utf-8")
    assert "Aggregated metrics" in html
    assert "crc32-check" in html
    assert "<script src" not in html
