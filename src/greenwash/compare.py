"""Paired comparison of two greenwash result directories.

Only attempts present in both runs (same task id and repeat index) are paired;
unpaired attempts are reported but never silently folded into the deltas. The
bootstrap CI is computed over the *pair differences*, which is the correct
unit of resampling for a paired design.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from greenwash.report import ReportError, load_report
from greenwash.runner import bootstrap_ci


class CompareError(ValueError):
    """Raised when two result sets cannot be paired."""


@dataclass(frozen=True)
class _Pair:
    task_id: str
    repeat: int
    a: dict[str, object]
    b: dict[str, object]


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


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


def _hidden(row: dict[str, object]) -> float:
    return 1.0 if _bool(row.get("hidden_pass")) else 0.0


def _greenwash(row: dict[str, object]) -> float:
    return 1.0 if _bool(row.get("greenwash")) else 0.0


def _partial(row: dict[str, object]) -> float:
    return _float(_dict(row.get("hidden")).get("score"))


def _visible(row: dict[str, object]) -> float:
    return 1.0 if _bool(row.get("visible_pass")) else 0.0


def _findings(row: dict[str, object]) -> float:
    return float(len(_list(_dict(row.get("tamper")).get("findings"))))


def _cost(row: dict[str, object]) -> float:
    return _float(row.get("cost_usd"))


def _tokens(row: dict[str, object]) -> float:
    return float(_int(row.get("tokens_in")) + _int(row.get("tokens_out")))


def _wall(row: dict[str, object]) -> float:
    return _float(row.get("wall_s"))


_MEASURES = {
    "hidden_pass_rate": _hidden,
    "greenwash_rate": _greenwash,
    "partial_hidden_score": _partial,
    "visible_pass_rate": _visible,
    "tamper_findings_per_attempt": _findings,
    "mean_cost_usd": _cost,
    "mean_tokens": _tokens,
    "mean_wall_s": _wall,
}


def _key(row: dict[str, object], label: str) -> tuple[str, int]:
    task_id = row.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise CompareError(f"{label}: missing task_id")
    repeat = row.get("repeat", 1)
    if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 1:
        raise CompareError(f"{label}: repeat must be a positive integer")
    return task_id, repeat


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def pair_records(
    a_records: tuple[dict[str, object], ...], b_records: tuple[dict[str, object], ...]
) -> dict[str, object]:
    """Compute paired deltas from two JSONL record sets (b minus a)."""
    left: dict[tuple[str, int], dict[str, object]] = {}
    right: dict[tuple[str, int], dict[str, object]] = {}
    for label, source_rows, target in (("a", a_records, left), ("b", b_records, right)):
        for index, row in enumerate(source_rows, start=1):
            key = _key(row, f"{label} record {index}")
            if key in target:
                raise CompareError(f"{label}: duplicate attempt for {key[0]} repeat {key[1]}")
            target[key] = row

    common = sorted(set(left) & set(right))
    pairs = tuple(
        _Pair(task_id, repeat, left[(task_id, repeat)], right[(task_id, repeat)])
        for task_id, repeat in common
    )
    n = len(pairs)
    deltas = {
        name: [float(measure(pair.b) - measure(pair.a)) for pair in pairs]
        for name, measure in _MEASURES.items()
    }
    a_values = {
        name: _mean([float(measure(pair.a)) for pair in pairs])
        for name, measure in _MEASURES.items()
    }
    b_values = {
        name: _mean([float(measure(pair.b)) for pair in pairs])
        for name, measure in _MEASURES.items()
    }

    better = sum(1 for pair in pairs if _hidden(pair.b) > _hidden(pair.a))
    worse = sum(1 for pair in pairs if _hidden(pair.b) < _hidden(pair.a))

    rows: list[dict[str, object]] = []
    for pair in pairs:
        rows.append(
            {
                "task_id": pair.task_id,
                "repeat": pair.repeat,
                "a_hidden_pass": _hidden(pair.a) == 1.0,
                "b_hidden_pass": _hidden(pair.b) == 1.0,
                "a_greenwash": _greenwash(pair.a) == 1.0,
                "b_greenwash": _greenwash(pair.b) == 1.0,
                "hidden_pass_delta": deltas["hidden_pass_rate"][len(rows)],
                "partial_score_delta": deltas["partial_hidden_score"][len(rows)],
                "greenwash_delta": deltas["greenwash_rate"][len(rows)],
                "tamper_delta": deltas["tamper_findings_per_attempt"][len(rows)],
                "cost_delta_usd": deltas["mean_cost_usd"][len(rows)],
            }
        )

    return {
        "paired_attempts": n,
        "tasks": sorted({pair.task_id for pair in pairs}),
        "unpaired_a": [f"{key[0]}#{key[1]}" for key in sorted(set(left) - set(right))],
        "unpaired_b": [f"{key[0]}#{key[1]}" for key in sorted(set(right) - set(left))],
        "a": a_values,
        "b": b_values,
        "delta": {
            name: {
                "mean": _mean(values),
                "ci95": bootstrap_ci(values),
            }
            for name, values in deltas.items()
        },
        "outcomes": {"b_better": better, "b_worse": worse, "tie": n - better - worse},
        "pairs": rows,
    }


def compare_dirs(a: Path, b: Path) -> dict[str, object]:
    """Load two result directories and return their paired comparison."""
    try:
        left, right = load_report(a), load_report(b)
    except ReportError as exc:
        raise CompareError(str(exc)) from exc
    return pair_records(left.records, right.records)


def write_compare(payload: dict[str, object], out_dir: Path) -> Path:
    """Persist a comparison as ``out_dir/compare.json``."""
    target = out_dir / "compare.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return target
