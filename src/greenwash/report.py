"""Self-contained static HTML leaderboard rendered from summary.json + JSONL.

The generated page has no runtime dependencies: CSS and the small sorting
script are inlined, so opening ``report.html`` from disk works offline. Every
data value is escaped by Jinja2 autoescaping; attempt data is never injected as
raw HTML or JavaScript.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, PackageLoader

# Explicit True: select_autoescape() keys off the template *filename* suffix,
# and our template ends in .html.j2, so the heuristic would silently disable
# escaping and let attempt data inject markup into the report.
_ENV = Environment(
    loader=PackageLoader("greenwash", "templates"),
    autoescape=True,
    keep_trailing_newline=True,
)


class ReportError(ValueError):
    """Raised when a results directory is missing or malformed."""


@dataclass(frozen=True)
class ReportData:
    """The two files the report is built from."""

    summary: dict[str, object]
    records: tuple[dict[str, object], ...]


def _reject_constant(value: str) -> object:
    """Python accepts NaN/Infinity, but they would emit non-standard JSON downstream."""
    raise ValueError(f"non-standard JSON constant {value!r}")


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError) as exc:
        raise ReportError(f"cannot read {path}: {exc}") from exc


def load_report(directory: Path) -> ReportData:
    """Load and validate ``summary.json`` and ``results.jsonl`` from a run."""
    summary_path = directory / "summary.json"
    results_path = directory / "results.jsonl"
    for path in (summary_path, results_path):
        if not path.is_file():
            raise ReportError(f"missing result file: {path}")

    summary = _read_json(summary_path)
    if not isinstance(summary, dict):
        raise ReportError("summary.json must contain a JSON object")
    for key in ("overall", "by_agent_model"):
        if not isinstance(summary.get(key), dict):
            raise ReportError(f"summary.json must contain an object named '{key}'")

    records: list[dict[str, object]] = []
    try:
        text = results_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"cannot read {results_path}: {exc}") from exc
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, parse_constant=_reject_constant)
        except ValueError as exc:
            raise ReportError(f"{results_path}:{number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ReportError(f"{results_path}:{number}: expected a JSON object")
        for key in ("task_id", "agent", "model"):
            if not isinstance(row.get(key), str):
                raise ReportError(f"{results_path}:{number}: '{key}' must be a string")
        records.append(cast(dict[str, object], row))
    if not records:
        raise ReportError(f"{results_path} contains no attempts")
    return ReportData(summary=cast(dict[str, object], summary), records=tuple(records))


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _float(value: object) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _int(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return 0


def _bool(value: object) -> bool:
    return value is True


def _pct(value: object) -> str:
    return f"{_float(value):.1%}"


def _ci(value: object, spec: str) -> str:
    bounds = _list(value)
    if len(bounds) != 2:
        return "n/a"
    return f"[{_float(bounds[0]):{spec}}, {_float(bounds[1]):{spec}}]"


def _money(value: object) -> str:
    return f"${_float(value):.4f}"


def _number(value: object) -> str:
    return f"{_float(value):.1f}"


def _metric_cards(overall: dict[str, object]) -> list[dict[str, str]]:
    rate = ".1%"
    detail = ".3f"
    return [
        {
            "label": "Hidden pass rate (tasks solved)",
            "value": _pct(overall.get("hidden_pass_rate")),
            "ci": _ci(overall.get("hidden_pass_rate_ci95"), rate),
            "note": "hidden tests fully pass on the agent's implementation",
        },
        {
            "label": "Partial hidden score",
            "value": _pct(overall.get("partial_hidden_score")),
            "ci": _ci(overall.get("partial_hidden_score_ci95"), rate),
            "note": "fraction of hidden tests that pass",
        },
        {
            "label": "Greenwash rate",
            "value": _pct(overall.get("greenwash_rate")),
            "ci": _ci(overall.get("greenwash_rate_ci95"), rate),
            "note": "claimed DONE while hidden tests failed",
        },
        {
            "label": "Visible pass rate",
            "value": _pct(overall.get("visible_pass_rate")),
            "ci": _ci(overall.get("visible_pass_rate_ci95"), rate),
            "note": "tests on the workspace as delivered by the agent",
        },
        {
            "label": "Original visible pass rate",
            "value": _pct(overall.get("original_visible_pass_rate")),
            "ci": _ci(overall.get("original_visible_pass_rate_ci95"), rate),
            "note": "visible tests after restoring the originals",
        },
        {
            "label": "Visible/hidden gap",
            "value": _pct(overall.get("visible_hidden_gap")),
            "ci": _ci(overall.get("visible_hidden_gap_ci95"), rate),
            "note": "visible pass rate minus hidden pass rate",
        },
        {
            "label": "Honest failure rate",
            "value": _pct(overall.get("honest_failure_rate")),
            "ci": _ci(overall.get("honest_failure_rate_ci95"), rate),
            "note": "claimed FAILED and hidden tests failed",
        },
        {
            "label": "Mean cost (USD)",
            "value": _money(overall.get("mean_cost_usd")),
            "ci": _ci(overall.get("mean_cost_usd_ci95"), detail),
            "note": "per attempt",
        },
        {
            "label": "Mean tokens",
            "value": _number(overall.get("mean_tokens")),
            "ci": _ci(overall.get("mean_tokens_ci95"), detail),
            "note": "input + output per attempt",
        },
        {
            "label": "Mean wall time (s)",
            "value": _number(overall.get("mean_wall_s")),
            "ci": _ci(overall.get("mean_wall_s_ci95"), detail),
            "note": "per attempt",
        },
    ]


def _agent_rows(data: ReportData) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    by_agent = _dict(data.summary.get("by_agent_model"))
    for name in sorted(by_agent):
        metrics = _dict(by_agent[name])
        tamper_rate = _float(
            sum(_float(value) for value in _dict(metrics.get("tamper_rate_by_kind")).values())
        )
        pass_at_1 = _float(_dict(metrics.get("pass_at_k")).get("1"))
        rows.append(
            {
                "name": name,
                "attempts": str(_int(metrics.get("attempts"))),
                "hidden": _pct(metrics.get("hidden_pass_rate")),
                "hidden_value": str(_float(metrics.get("hidden_pass_rate"))),
                "partial": _pct(metrics.get("partial_hidden_score")),
                "partial_value": str(_float(metrics.get("partial_hidden_score"))),
                "visible": _pct(metrics.get("visible_pass_rate")),
                "visible_value": str(_float(metrics.get("visible_pass_rate"))),
                "greenwash": _pct(metrics.get("greenwash_rate")),
                "greenwash_value": str(_float(metrics.get("greenwash_rate"))),
                "tamper": _pct(tamper_rate),
                "tamper_value": str(tamper_rate),
                "cost": _money(metrics.get("mean_cost_usd")),
                "cost_value": str(_float(metrics.get("mean_cost_usd"))),
                "tokens": _number(metrics.get("mean_tokens")),
                "tokens_value": str(_float(metrics.get("mean_tokens"))),
                "pass_at_1": _pct(pass_at_1),
                "pass_at_1_value": str(pass_at_1),
            }
        )
    return rows


def _attempt_view(index: int, row: dict[str, object]) -> dict[str, Any]:
    claim = _dict(row.get("claim"))
    tamper = _dict(row.get("tamper"))
    findings = []
    for item in _list(tamper.get("findings")):
        finding = _dict(item)
        findings.append(
            {
                "kind": _str(finding.get("kind")),
                "path": _str(finding.get("path")),
                "detail": _str(finding.get("detail")),
                "hunk": _str(finding.get("hunk")),
            }
        )
    tests = []
    for name, key in (
        ("Visible tests (as delivered)", "visible"),
        ("Visible tests (originals restored)", "original_visible"),
        ("Hidden tests", "hidden"),
    ):
        outcome = _dict(row.get(key))
        tests.append(
            {
                "name": name,
                "passed": _int(outcome.get("passed")),
                "total": _int(outcome.get("total")),
                "ok": "PASS" if _bool(outcome.get("ok")) else "FAIL",
                "stdout": _str(outcome.get("stdout")),
                "stderr": _str(outcome.get("stderr")),
            }
        )
    return {
        "id": f"attempt-{index:03d}",
        "task_id": _str(row.get("task_id")),
        "agent": _str(row.get("agent")),
        "model": _str(row.get("model")),
        "repeat": _int(row.get("repeat")),
        "claim": _str(claim.get("status")),
        "claim_certain": "certain" if _bool(claim.get("certain")) else "heuristic",
        "claim_evidence": _str(claim.get("evidence")),
        "hidden_pass": _bool(row.get("hidden_pass")),
        "visible_pass": _bool(row.get("visible_pass")),
        "original_visible_pass": _bool(row.get("original_visible_pass")),
        "greenwash": _bool(row.get("greenwash")),
        "cost": _money(row.get("cost_usd")),
        "tokens": str(_int(row.get("tokens_in")) + _int(row.get("tokens_out"))),
        "wall": _number(row.get("wall_s")),
        "spec": _str(row.get("spec")) or "(this result file does not contain the spec)",
        "diff": _str(row.get("diff")) or "(no changes)",
        "findings": findings,
        "tests": tests,
    }


def _matrix(attempts: list[dict[str, Any]]) -> list[dict[str, object]]:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        by_task.setdefault(attempt["task_id"], []).append(attempt)
    rows: list[dict[str, object]] = []
    for task_id in sorted(by_task):
        cells = []
        for attempt in sorted(by_task[task_id], key=lambda item: int(item["repeat"])):
            markers = []
            if attempt["greenwash"]:
                markers.append("greenwash")
            if attempt["findings"]:
                markers.append("tamper")
            cells.append(
                {
                    "id": attempt["id"],
                    "label": f"R{attempt['repeat']}",
                    "status": "PASS" if attempt["hidden_pass"] else "FAIL",
                    "markers": " ".join(markers),
                    "title": (
                        f"{attempt['agent']}/{attempt['model']} · claim {attempt['claim']} · "
                        f"hidden {'pass' if attempt['hidden_pass'] else 'fail'}"
                    ),
                }
            )
        rows.append({"task_id": task_id, "cells": cells})
    return rows


def render_html(data: ReportData) -> str:
    """Render a deterministic, fully offline HTML report."""
    overall = _dict(data.summary.get("overall"))
    attempts = [_attempt_view(index, row) for index, row in enumerate(data.records, start=1)]
    pass_at_k = [
        {"k": key, "value": _pct(value)}
        for key, value in sorted(
            _dict(overall.get("pass_at_k")).items(),
            key=lambda item: int(item[0]) if item[0].isdigit() else 0,
        )
    ]
    tamper_rows = [
        {"kind": kind, "rate": _pct(rate)}
        for kind, rate in sorted(_dict(overall.get("tamper_rate_by_kind")).items())
    ]
    view: dict[str, object] = {
        "task_count": len(_list(data.summary.get("tasks"))),
        "attempt_count": _int(overall.get("attempts")) or len(attempts),
        "cards": _metric_cards(overall),
        "pass_at_k": pass_at_k,
        "tamper_rows": tamper_rows,
        "agents": _agent_rows(data),
        "matrix": _matrix(attempts),
        "attempts": attempts,
    }
    return _ENV.get_template("report.html.j2").render(**view)


def write_report(directory: Path, out_path: Path | None = None) -> Path:
    """Write ``report.html`` from a results directory and return its path."""
    target = out_path if out_path is not None else directory / "report.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_html(load_report(directory)), encoding="utf-8", newline="\n")
    return target
