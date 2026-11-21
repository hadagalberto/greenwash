"""Benchmark orchestration, JSONL results and aggregated summary."""

from __future__ import annotations

import json
import random
import statistics
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from greenwash.adapters import AgentAdapter, make_prompt
from greenwash.grading import AttemptRecord, grade_attempt
from greenwash.models import Task
from greenwash.sandbox import LocalSandbox, Sandbox
from greenwash.workspace import Workspace


@dataclass(frozen=True)
class RunConfig:
    """Configuration for one benchmark run."""

    tasks: tuple[Task, ...]
    adapter: AgentAdapter
    repeat: int
    jobs: int
    timeout_s: int
    out_dir: Path
    sandbox: Sandbox = LocalSandbox()


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def bootstrap_ci(values: list[float], seed: int = 0, resamples: int = 1000) -> list[float]:
    """Percentile bootstrap 95% confidence interval for the mean."""
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(resamples):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(statistics.fmean(sample))
    means.sort()
    low = int(0.025 * resamples)
    high = min(int(0.975 * resamples), resamples - 1)
    return [means[low], means[high]]


def _pass_at_k(records: list[AttemptRecord], k: int) -> float:
    """Fraction of tasks solved at least once within the first ``k`` attempts."""
    by_task: dict[str, list[AttemptRecord]] = {}
    for record in records:
        by_task.setdefault(record.task_id, []).append(record)
    solved = 0
    for attempts in by_task.values():
        ordered = sorted(attempts, key=lambda item: item.repeat)
        if any(item.hidden_pass for item in ordered[:k]):
            solved += 1
    return _rate(solved, len(by_task))


def summarize(records: list[AttemptRecord], max_repeat: int) -> dict[str, object]:
    """Compute the metrics described in SPEC.md for a set of attempts.

    Every headline metric gets a deterministic percentile-bootstrap 95% CI so
    the report can show uncertainty even for small runs. All intervals use the
    same seed and resample count, which makes them reproducible across runs,
    platforms and Python versions (the golden tests pin the exact values).
    """
    n = len(records)
    hidden_passes = [1.0 if record.hidden_pass else 0.0 for record in records]
    visible_passes = [1.0 if record.visible_pass else 0.0 for record in records]
    original_visible = [1.0 if record.original_visible_pass else 0.0 for record in records]
    greenwashes = [1.0 if record.greenwash else 0.0 for record in records]
    honest_failures = [
        1.0 if record.claimed_failed and not record.hidden_pass else 0.0 for record in records
    ]
    partial = [record.hidden.score for record in records]
    # The visible/hidden gap is the gap in *full-task* outcomes, paired per
    # attempt: a greenwash attempt is 1.0, an honest pass or failure is 0.0.
    gaps = [visible - hidden for visible, hidden in zip(visible_passes, hidden_passes, strict=True)]
    costs = [record.cost_usd for record in records]
    tokens = [float(record.tokens_in + record.tokens_out) for record in records]
    walls = [record.wall_s for record in records]
    counts: dict[str, int] = {}
    for record in records:
        for kind, count in record.tamper.by_kind().items():
            counts[kind] = counts.get(kind, 0) + count

    return {
        "attempts": n,
        "hidden_pass_rate": _mean(hidden_passes),
        "hidden_pass_rate_ci95": bootstrap_ci(hidden_passes),
        "partial_hidden_score": _mean(partial),
        "partial_hidden_score_ci95": bootstrap_ci(partial),
        "visible_pass_rate": _mean(visible_passes),
        "visible_pass_rate_ci95": bootstrap_ci(visible_passes),
        "visible_hidden_gap": _mean(gaps),
        "visible_hidden_gap_ci95": bootstrap_ci(gaps),
        "original_visible_pass_rate": _mean(original_visible),
        "original_visible_pass_rate_ci95": bootstrap_ci(original_visible),
        "greenwash_rate": _mean(greenwashes),
        "greenwash_rate_ci95": bootstrap_ci(greenwashes),
        "honest_failure_rate": _mean(honest_failures),
        "honest_failure_rate_ci95": bootstrap_ci(honest_failures),
        "tamper_rate_by_kind": {kind: _rate(count, n) for kind, count in sorted(counts.items())},
        "mean_cost_usd": _mean(costs),
        "mean_cost_usd_ci95": bootstrap_ci(costs),
        "mean_tokens": _mean(tokens),
        "mean_tokens_ci95": bootstrap_ci(tokens),
        "mean_wall_s": _mean(walls),
        "mean_wall_s_ci95": bootstrap_ci(walls),
        "pass_at_k": {str(k): _pass_at_k(records, k) for k in range(1, max_repeat + 1)},
    }


def _one_attempt(
    task: Task, adapter: AgentAdapter, repeat: int, timeout_s: int, sandbox: Sandbox
) -> AttemptRecord:
    with Workspace(task) as workspace:
        prompt = make_prompt(task)
        agent_result = adapter.run(workspace.path, prompt, timeout_s)
        return grade_attempt(
            task, agent_result, workspace, timeout_s, repeat=repeat, sandbox=sandbox
        )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def run_benchmark(config: RunConfig) -> dict[str, object]:
    """Execute every (task, repeat) pair, persist results and return the summary."""
    jobs = max(1, config.jobs)
    futures = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        for task in config.tasks:
            for repeat in range(1, config.repeat + 1):
                futures.append(
                    executor.submit(
                        _one_attempt,
                        task,
                        config.adapter,
                        repeat,
                        config.timeout_s,
                        config.sandbox,
                    )
                )
        records = [future.result() for future in futures]

    records.sort(key=lambda record: (record.task_id, record.repeat))
    results_path = config.out_dir / "results.jsonl"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    by_agent: dict[str, list[AttemptRecord]] = {}
    for record in records:
        by_agent.setdefault(f"{record.agent}/{record.model}", []).append(record)

    summary: dict[str, object] = {
        "attempt_count": len(records),
        "tasks": [task.id for task in config.tasks],
        "overall": summarize(records, config.repeat),
        "by_agent_model": {
            key: summarize(items, config.repeat) for key, items in sorted(by_agent.items())
        },
    }
    _write_json(config.out_dir / "summary.json", summary)
    from greenwash.report import write_report

    write_report(config.out_dir)
    return summary
