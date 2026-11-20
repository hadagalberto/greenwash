"""Command-line interface for greenwash."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from greenwash.adapters import AdapterUnavailableError, resolve_adapter
from greenwash.models import Task
from greenwash.runner import RunConfig, run_benchmark
from greenwash.tasks import TaskError, discover_tasks
from greenwash.validate import validate_all

_DEFAULT_TASKS = Path(__file__).resolve().parents[2] / "tasks"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greenwash",
        description="Measure whether coding agents tell the truth when they say all tests pass.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-tasks", help="validate every task's oracle strength")
    validate.add_argument("--tasks", type=Path, default=_DEFAULT_TASKS)
    validate.add_argument("--glob", default="*", help="only validate matching task ids")
    validate.add_argument("--timeout", type=int, default=None)

    run = sub.add_parser("run", help="run the benchmark against an agent")
    run.add_argument("--agent", required=True, help="adapter name: command or scripted")
    run.add_argument("--model", default="command", help="model id recorded in results")
    run.add_argument(
        "--agent-cmd", default=None, help="command template with {workdir} {prompt_file}"
    )
    run.add_argument(
        "--script", type=Path, default=None, help="JSON script for the scripted adapter"
    )
    run.add_argument("--tasks", type=Path, default=_DEFAULT_TASKS)
    run.add_argument("--glob", default="*")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--jobs", type=int, default=1)
    run.add_argument("--timeout", type=int, default=None)
    run.add_argument("--out", type=Path, default=Path("results"))
    return parser


def _load_tasks(path: Path, pattern: str) -> tuple[Task, ...]:
    try:
        return discover_tasks(path, pattern)
    except TaskError as exc:
        raise SystemExit(f"error: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = _parser().parse_args(argv)

    if args.command == "validate-tasks":
        tasks = _load_tasks(args.tasks, args.glob)
        if not tasks:
            print(f"error: no tasks found under {args.tasks}")
            return 2
        ok, problems = validate_all([task.root for task in tasks], timeout_s=args.timeout)
        if ok:
            print(f"validated {len(tasks)} task(s): all oracles passed")
            return 0
        for problem in problems:
            print(f"FAIL: {problem}")
        print(f"{len(problems)} violation(s)")
        return 1

    tasks = _load_tasks(args.tasks, args.glob)
    if not tasks:
        print(f"error: no tasks found under {args.tasks}")
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1")
        return 2
    try:
        adapter = resolve_adapter(args.agent, args.agent_cmd, args.script, model=args.model)
    except AdapterUnavailableError as exc:
        print(f"error: {exc}")
        return 2

    timeout = (
        args.timeout if args.timeout is not None else max(task.time_budget_s for task in tasks)
    )
    summary = run_benchmark(
        RunConfig(
            tasks=tasks,
            adapter=adapter,
            repeat=args.repeat,
            jobs=max(1, args.jobs),
            timeout_s=timeout,
            out_dir=args.out,
        )
    )
    overall = summary["overall"]
    assert isinstance(overall, dict)
    print(json.dumps({"overall": overall, "results": str(args.out / "results.jsonl")}, indent=2))
    return 0
