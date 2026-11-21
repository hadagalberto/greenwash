"""Command-line interface for greenwash."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from greenwash.adapters import AdapterUnavailableError, available_adapters, resolve_adapter
from greenwash.compare import CompareError, compare_dirs, write_compare
from greenwash.models import Task
from greenwash.pricing import PriceTableError
from greenwash.runner import RunConfig, run_benchmark
from greenwash.sandbox import DEFAULT_SANDBOX_IMAGE, build_sandbox
from greenwash.tasks import TaskError, discover_tasks
from greenwash.validate import validate_all

# An installed wheel carries the tasks under ``greenwash/tasks``; a source
# checkout keeps them at the repository root.  Support both (finding 18).
_PACKAGE_TASKS = Path(__file__).resolve().parent / "tasks"
_REPO_TASKS = Path(__file__).resolve().parents[2] / "tasks"
_DEFAULT_TASKS = _PACKAGE_TASKS if _PACKAGE_TASKS.is_dir() else _REPO_TASKS
_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"
_DEFAULT_MAX_STEPS = 30


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

    compare = sub.add_parser("compare", help="paired comparison of two result directories")
    compare.add_argument("a", type=Path, help="baseline result directory")
    compare.add_argument("b", type=Path, help="candidate result directory")
    compare.add_argument(
        "--out", type=Path, default=None, help="optional directory for compare.json"
    )

    run = sub.add_parser("run", help="run the benchmark against an agent")
    run.add_argument(
        "--agent",
        required=True,
        help=f"adapter: {', '.join(sorted(available_adapters()))}",
    )
    run.add_argument("--model", default=None, help="model id (required for the builtin adapter)")
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
    run.add_argument(
        "--base-url",
        default=_DEFAULT_BASE_URL,
        help="OpenAI-compatible base URL used by the builtin adapter",
    )
    run.add_argument(
        "--api-key-env",
        default=_DEFAULT_API_KEY_ENV,
        help="environment variable holding the API key for the builtin adapter",
    )
    run.add_argument(
        "--max-steps", type=int, default=_DEFAULT_MAX_STEPS, help="builtin agent tool-round limit"
    )
    run.add_argument(
        "--price-table", type=Path, default=None, help="versioned JSON price table for the builtin"
    )
    run.add_argument("--sandbox", default="local", help="execution backend: local or docker")
    run.add_argument(
        "--sandbox-image",
        default=DEFAULT_SANDBOX_IMAGE,
        help=f"container image for --sandbox docker (default: {DEFAULT_SANDBOX_IMAGE})",
    )
    return parser


def _load_tasks(path: Path, pattern: str) -> tuple[Task, ...]:
    try:
        return discover_tasks(path, pattern)
    except TaskError as exc:
        raise SystemExit(f"error: {exc}") from exc


def _check_out_dir(path: Path) -> bool:
    """Reject an existing file used as an output directory with a clear error."""
    if path.exists() and not path.is_dir():
        print(f"error: --out must be a directory: {path}")
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = _parser().parse_args(argv)
    if getattr(args, "timeout", None) is not None and args.timeout < 1:
        # A non-positive timeout makes every subprocess time out instantly,
        # which looks like every oracle failed instead of a bad invocation.
        print("error: --timeout must be >= 1")
        return 2

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

    if args.command == "compare":
        if args.out is not None and not _check_out_dir(args.out):
            return 2
        try:
            result = compare_dirs(args.a, args.b)
        except CompareError as exc:
            print(f"error: {exc}")
            return 2
        if args.out is not None:
            write_compare(result, args.out)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if not _check_out_dir(args.out):
        return 2
    tasks = _load_tasks(args.tasks, args.glob)
    if not tasks:
        print(f"error: no tasks found under {args.tasks}")
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1")
        return 2
    if args.max_steps < 1:
        print("error: --max-steps must be >= 1")
        return 2
    try:
        sandbox = build_sandbox(args.sandbox, args.sandbox_image)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    if sandbox.name == "local":
        print(
            "warning: agents run commands on the host in temporary directories; "
            "hidden tests and references are readable on the host in local mode; "
            "use --sandbox docker for isolation",
            file=sys.stderr,
        )
    try:
        adapter = resolve_adapter(
            args.agent,
            args.agent_cmd,
            args.script,
            model=args.model,
            sandbox=sandbox,
            base_url=args.base_url,
            api_key_env=args.api_key_env,
            max_steps=args.max_steps,
            price_table=args.price_table,
        )
    except (AdapterUnavailableError, PriceTableError) as exc:
        print(f"error: {exc}")
        return 2

    # Finding 18: honour each task's declared time_budget_s unless the user
    # explicitly passed --timeout.  The global value is only a fallback.
    timeout = (
        args.timeout if args.timeout is not None else max(task.time_budget_s for task in tasks)
    )
    task_timeouts: dict[str, int] = {}
    if args.timeout is None:
        task_timeouts = {task.id: task.time_budget_s for task in tasks}
    summary = run_benchmark(
        RunConfig(
            tasks=tasks,
            adapter=adapter,
            repeat=args.repeat,
            jobs=max(1, args.jobs),
            timeout_s=timeout,
            out_dir=args.out,
            sandbox=sandbox,
            task_timeouts=task_timeouts,
        )
    )
    overall = summary["overall"]
    assert isinstance(overall, dict)
    print(
        json.dumps(
            {
                "overall": overall,
                "results": str(args.out / "results.jsonl"),
                "summary": str(args.out / "summary.json"),
                "report": str(args.out / "report.html"),
            },
            indent=2,
        )
    )
    return 0
