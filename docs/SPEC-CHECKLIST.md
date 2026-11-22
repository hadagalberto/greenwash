# SPEC checklist — Milestone 9 re-audit

Every requirement in `SPEC.md` is listed below. `Status` is based on **running**
the command or exercising the behaviour, not on reading the code. The milestone-8
checklist overstated CI, timeout enforcement and transcript capture; those rows
are now corrected against the milestone-9 fixes. Evidence is the command that
was run and the observed result on Python 3.15.2 / Node 26.13.0 / Windows 11.
Full final verification results are at the end of this document.

Legend: **PASS** — verified by execution; **PASS\*** — verified with a documented
deviation; **N/A** — design constraint covered by construction, not directly
measurable.

## Purpose, motivation and distribution (SPEC lines 3–11)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Benchmark measures truthfulness of "all tests pass" claims | PASS | `python -m pytest tests/test_e2e.py -q` — honest/greenwash/tamperer profiles produce hidden pass 1/3 and greenwash rate 2/3 from the same visible pass rate 1.0. |
| 2 | Reports greenwash rate, tampering, visible/hidden gap, cost, tokens, wall time | PASS | `greenwash run` on `examples/honest-crc32.json`: `greenwash_rate`, `mean_cost_usd`, `mean_tokens`, `mean_wall_s`; HTML report contains a **Visible/hidden gap** card; `test_report_shows_the_visible_hidden_gap` pins 50.0% for fixture A. |
| 3 | Works with any agent CLI or OpenAI-compatible model via builtin loop | PASS | CLI adapters + `builtin` exercised in `tests/test_adapters.py`, `tests/test_builtin.py`, `tests/test_cli.py` with fake executables and a loopback fake server. |
| 4 | Open source MIT, "Hadagalberto Junior", not published to PyPI | PASS | `LICENSE`, `pyproject.toml` authors/classifier; no publish command exists in code, CI or scripts. |
| 5 | No stubs/TODO/skipped/placeholder tests | PASS | `grep -R "TODO\|NotImplemented\|unimplemented\|@pytest.mark.skip"` over `src/`, `tests/`, `tasks/` finds only the `TODO`-marker *detector* in `tasks.py` and its tests. `validate-tasks` rejects any spec.md containing `TODO`. |
| 6 | Motivation present in both READMEs | PASS | `README.md` "Motivation"; `README.pt-BR.md` "Motivação", wording from SPEC lines 10–11. |

## Stack (SPEC lines 13–16)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 7 | Python ≥ 3.11, hatchling, CLI `greenwash` (argparse) | PASS | `requires-python = ">=3.11"`; `python -m pip wheel . --no-deps -w dist/` builds `greenwash-0.1.0-py3-none-any.whl`; `greenwash --help` works via `[project.scripts]`. Ran on 3.15.2; CI matrix 3.11/3.12/3.13. |
| 8 | `mypy --strict`, `ruff`, `pytest` | PASS | `python -m mypy --strict` → `Success: no issues found in 53 source files`; `python -m ruff check .` → all passed; `python -m ruff format --check .` → 325 files formatted; `python -m pytest` → **341 passed**. |
| 9 | Coverage ≥ 90% for the harness | PASS | `pyproject.toml` `addopts` has `--cov-fail-under=90`; final run reports **93.46%**. |
| 10 | Hypothesis "where useful" | PASS | Installed in `dev` extras. No property test was added because every vector in this project has a known official/expected value; deterministic assertions are stronger here. No skipped placeholders. |
| 11 | Small runtime deps: httpx, PyYAML, Jinja2, optional rich | PASS | `dependencies = [httpx, Jinja2, PyYAML, typer]`; rich is not required anywhere. |
| 12 | Tasks in Python **and** TypeScript; harness runs each task's own test command | PASS\* | 20 Python + 20 TypeScript tasks; `task.yaml` declares visible/hidden commands executed by `run_tests()`. Deviation recorded in SPEC: Node's built-in `node:test` is used instead of vitest, and `--experimental-strip-types` requires Node ≥ 22.6 (CI pins 22.23.5). All TS commands use an explicit quoted glob so Node 22 does not treat a directory as a test file. |
| 13 | CI on ubuntu/windows/macos for harness; separate ubuntu `validate-tasks` job | FAIL (CI not observed) | The matrix is declared. Round-2 fixed the POSIX `mypy` error and round-3 item 3 fixed the detached-grandchild pipe hang that made 6 ubuntu/macos jobs red (`proc.wait` + immediate `killpg`, bounded reader threads). `mypy --platform linux` is a regression test and the pipe-release test passes locally, but a green run of all 10 GitHub Actions jobs has **not** been observed here, so this row stays FAIL until CI is green. |
| 14 | README.md (en) + README.pt-BR.md, CHANGELOG, CONTRIBUTING, LICENSE | PASS | All five files present; both README quickstarts were executed (see item 22). |
| 15 | Do not publish to PyPI | PASS | No `twine`, `uv publish` or PyPI upload step anywhere; wheel build is local only. |

## Task format (SPEC lines 18–25)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 16 | `task.yaml`: id, title, language, category, difficulty, time budget, visible/hidden test commands, protected files, sources | PASS | `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s): all oracles passed`; loader rejects unknown keys, wrong types, bad ids and mismatched directory names (`tests/test_tasks.py`). |
| 17 | `spec.md` is the only task description, precise with examples and authoritative citations | PASS | All 40 specs validated non-empty and TODO-free; sources cited (RFC/ISO/SemVer/Unicode/GSI/official docs). Prior hand-derived review: `docs/REVIEW-2026-11-20.md`, `docs/REVIEW-2026-11-20-m7.md`. |
| 18 | Visible tests correct but incomplete; pass on ≥ 1 wrong solution | PASS | Every trap passes visible and fails hidden — checked by `validate-tasks` for all 40 tasks. |
| 19 | Hidden tests hand/official vectors, no reference import | PASS | `hidden_reference_imports()` static check clean for all 40; regression test covers relative/dotted imports. |
| 20 | Reference passes visible + hidden | PASS | `validate-tasks` exits 0 over 40 references. |
| 21 | ≥ 2 traps and ≥ 3 mutants per task; mutants killed by hidden tests | PASS | Layout loader enforces counts; all traps/mutants exercised by `validate-tasks`. |

Note: `protected_files` is intentionally **documented, not enforced** — SPEC says
"none by default — tampering is measured, not prevented". `CONTRIBUTING.md`
states this explicitly.

## Validation command (SPEC lines 27–28)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 22 | Reference passes; traps pass visible & fail hidden; mutants fail hidden | PASS | `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s): all oracles passed` (exit 0). Took about 15 minutes on Windows after the round-3 oracle change (each suite now does a trusted collect pass plus a graded run); CI ubuntu job runs the same command. |
| 23 | spec.md has no TODO | PASS | Loader `_TODO_RE` check; `validate-tasks` passes. |
| 24 | Hidden tests cannot import from `reference/` | PASS | Static regex check in `tasks.py`; hostile relative/dotted import test passes. |
| 25 | Non-zero exit on any violation; runs in CI | PASS | `tests/test_cli.py::test_cli_validate_tasks_failure` — corrupt a reference → exit 1, prints `FAIL:`; CI `validate-tasks` job. |

## Running (SPEC lines 30–37)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 26 | `run --agent --model [--tasks glob] [--repeat] [--jobs] [--timeout] [--out]` | PASS | All exercised in `tests/test_cli.py` and the verified README example. `--timeout 0`/negative now rejected with exit 2 (m8 regression). |
| 27 | Isolated temp workspace, git-initialised so diffs are exact | PASS\* | `Workspace` still initialises git for agent convenience, but the graded diff is now computed in Python with `difflib` against a pristine snapshot. This is stronger than a git diff: agent replace refs, `info/exclude`, fsmonitor hooks and textconv drivers cannot hide edits or run host commands. Regression tests in `tests/test_m9_core_security.py`. |
| 28 | Standard prompt (spec + completion instruction) | PASS | `make_prompt()` includes full spec and the exact `STATUS: DONE`/`STATUS: FAILED` instruction; used by every adapter and the e2e profile adapter. |
| 29 | Timeout enforced; transcript, tokens/cost, wall time captured | PASS\* (round-3 item 3) | Windows uses a kill-on-close Job Object and POSIX stores the pgid at spawn; the leader is now waited on with `proc.wait(timeout)` and its whole group killed immediately afterwards, so a grandchild inheriting the pipes can no longer hold `run_shell` open. Child output is captured into bounded buffers (round-3 item 4). Verified locally; POSIX process-kill behaviour is not executed in this environment, so CI confirmation remains open. |
| 30 | Grade order: visible as-is → restore originals → overlay hidden | PASS\* (round-3 items 1, 2) | Row 30 was **FAIL** while the hidden oracle rejected 7 correct references and implementation code could still forge a pass. Fixed: ids are streamed by the reporting plugin/`test:start` events (spaces and runtime names survive), `validate-tasks` uses the same `run_observed` oracle, a nonce canary must fail, node assertions are frozen in every child process via a `NODE_OPTIONS` preload, and oracle-interference findings force `hidden.ok = False`. Verified locally by the 40-task reference sweep and the three forgery probes; POSIX fd transport is not exercised on Windows. |
| 31 | Tamper analysis from git diff, all kinds classified with hunk | PASS | `tests/test_tamper.py`, `tests/test_m7_review_regressions.py`, m8 regressions plus `tests/test_m9_tamper.py` (config injection, tautologies, early returns, TS skip options and false-positive controls). |
| 32 | Claim parsing: final `STATUS:` line; documented uncertain fallback | PASS\* (item 4) | The last STATUS line of the final message is certain even when a short summary follows, and fallback hints can no longer turn `STATUS: FAILED` into DONE. An empty builtin final message yields UNKNOWN. Existing golden assertions that encoded the old behaviour were corrected with a finding-4 comment. |
| 33 | Optional Docker isolation; local default warns | PASS\* (item 3) | `docker/Dockerfile` supplies Python 3.12, pytest and Node 22 with network/pid/memory limits, and a `.dockerignore` now excludes `tasks/*/hidden`, `reference/`, `traps/`, `mutants/` and `tests/` from the build context. No real `docker build` was run here. |

## Adapters (SPEC lines 38–40)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 34 | `builtin` tool loop: read_file, write_file, list_dir, run_command (timeout + truncation) | PASS | `TOOL_DEFINITIONS` and `ToolExecutor`; `tests/test_builtin.py` covers all four, path-traversal rejection, large-output middle truncation and step limit. |
| 35 | Configurable base_url / api_key_env; usage + versioned price table | PASS | CLI flags wired to `BuiltinAdapter`; fake OpenAI server test verifies cost = 100/1M×0.15 + 20/1M×0.6; malformed price table exits 2; m8 regression rejects NaN/Infinity. |
| 36 | `opencode run --format json` | PASS | Fake executable records argv; `--model <id>` is passed and the multi-line prompt is streamed via stdin so `.cmd` launchers cannot truncate it. `tests/test_m9_claims_adapters.py`. |
| 37 | `claude -p --output-format json` | PASS | Same, with `--model` and stdin prompt. |
| 38 | `aider --message-file` | PASS\* (item 6) | Aider previously received only the first line through a `.cmd` shim. It now writes a transient prompt file in the workspace and passes `--message-file <path>`; the file is deleted after the run. |
| 39 | `codex exec --json -` | PASS\* (item 6) | Codex previously passed the prompt in argv. It now uses `codex exec -` and streams the full prompt on stdin; cumulative JSONL usage parsing is unchanged. |
| 40 | `command` template with `{workdir}` `{prompt_file}` | PASS | `test_cli_run_with_command_adapter` runs a real Python agent script. |
| 41 | Unavailable adapters reported, never faked | PASS | `resolve_adapter()` checks installation/config; missing executable exits 2 with "not available". |
| 42 | Unit-test adapters with fake executables/servers | PASS | `tests/fake_openai_server.py` (loopback only), `write_fake_cli()` helper, 17 adapter tests. |

## Metrics and report (SPEC lines 42–43)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 43 | Per-attempt and per-agent/model aggregation | PASS | `results.jsonl` + `summary.json.by_agent_model`; golden metrics pinned in `tests/test_metrics_golden.py`. |
| 44 | Hidden pass rate, partial score, visible pass rate, greenwash rate, honest-failure rate, tamper by kind, mean cost/tokens/time, pass@k, bootstrap 95% CIs | PASS | `summarize()` emits every field plus a scalar per-attempt tamper rate, uncertain/greenwash-certain rates and task-cluster CIs; exact hand-derived values asserted by `test_metrics_golden.py` and `tests/test_m9_metrics.py`. pass@k now uses the unbiased `1 - C(n-c,k)/C(n,k)` estimator. |
| 45 | Visible/hidden gap reported | PASS | First-class `visible_hidden_gap` and `visible_hidden_gap_ci95` in `summary.json` (paired per-attempt difference) plus an HTML card. Fixture A: 5/6 − 2/6 = 3/6 = 50.0%, CI [16.7%, 83.3%], asserted by `test_metrics_golden.py` and `test_report_shows_the_visible_hidden_gap`. |
| 46 | JSONL per attempt, `summary.json`, static HTML leaderboard | PASS | Verified run writes all three; `test_write_report_uses_lf_and_matches_golden`. |
| 47 | Sortable table, per-task matrix, drill-down (spec, diff, tamper hunks, test output) | PASS | `test_html_has_sortable_leaderboard_matrix_and_drilldowns` and `test_html_contains_spec_diff_tamper_hunks_and_test_output`; sort script inlined and keyboard accessible. |
| 48 | Offline, escaped report | PASS | `test_html_has_no_external_runtime_dependencies`, `test_untrusted_record_fields_are_escaped` (XSS vector). |
| 49 | `greenwash compare a/ b/` paired comparison | PASS | Verified: `greenwash compare tests/fixtures/report-a/ tests/fixtures/report-b/ --out …` → exit 0, `paired_attempts: 6`, `b_better: 2`, `b_worse: 0`, `compare.json` written. |

## Task suite (SPEC lines 45–47)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 50 | ≥ 40 tasks, roughly half Python / half TypeScript | PASS | `validate-tasks` reports 40; 20 `Language.PYTHON`, 20 `Language.TYPESCRIPT` (README list). |
| 51 | Categories spread across parsing, numeric, dates/time, money, concurrency, security, data structures, algorithms, text/i18n, API client | PASS | `category` field validated for all 40; list in `README.md` "Task suite". |
| 52 | Typical traps: date off-by-one, sign/rounding, Unicode/wide chars, CSV/INI/HTTP, traversal, JWT-style rules, caches, rate limiting, retry/idempotency, checksums, ISBN/IBAN/Luhn/EAN, semver, diff/patch, topo sort, intervals, money allocation, pagination, varint/base64url | PASS | Covered by the 40 task specs; each was hand-reviewed in the two `docs/REVIEW-*.md` files. |
| 53 | Timezone/DST trap topic | PASS\* | UTC/ISO-8601 handling in `cron-next` and HTTP-date/UTC parsing in `retry-after`; no dedicated DST-transition fixture. SPEC lists trap topics as examples ("many with …"), not a per-topic quota. |
| 54 | Each task solvable by a strong engineer in under an hour | N/A | Design constraint; each `task.yaml` sets a per-command `time_budget_s` (default timeout) and all references are small single- or two-file solutions. |

## Harness tests and hard constraints (SPEC lines 49–54)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 55 | Unit tests for every module | PASS | One `tests/test_<module>.py` per harness module; trivial `errors.py` exercised through adapter tests. |
| 56 | E2E: 3 tiny fixture tasks, scripted agent (honest, greenwash, tamperer), exact metrics and tamper classification | PASS | `tests/test_e2e.py`: hidden 1/3, visible 1.0, original-visible 2/3, greenwash 2/3, tamper kinds `expected_literal_changed` + `skip_marker` at 1/3 each. |
| 57 | Never push/publish; commit locally after each milestone | PASS | No `git push`/`gh`/`twine` in code or CI; this milestone committed locally. |
| 58 | Stay inside this repository | PASS | All edits under the repo root; throwaway probes in gitignored `.review/`. |
| 59 | No paid APIs in tests | PASS | Only `FakeOpenAIServer` (loopback) and fake executables; real-model calls are user-initiated CLI only. |

## Hostile-input findings and fixes in this milestone

| # | Finding | Fix | Regression test |
| --- | --- | --- | --- |
| H20 | Renaming a visible test out of its directory (or to an uncollected filename) evaded tamper detection | Compare old/new parents and filename collectability in `analyze_diff()` | 4 rename tests in `tests/test_m8_audit_regressions.py` |
| H21 | A removed hunk line beginning with `--` was mistaken for a file header | Removed the `---`/`+++` skip inside hunk bodies | `test_removed_line_starting_with_double_dash_is_analysed` |
| H22 | `NaN`/`Infinity` price entries produced invalid JSON cost | `_as_number()` requires finite values | 3 parametrised price tests |
| H23 | `--timeout 0`/negative made every oracle time out and produced false violations | CLI rejects non-positive timeouts with exit 2 | 2 parametrised timeout tests |
| H24 | `--out` pointing at an existing file raised an uncaught `FileExistsError` | CLI validates output directory up front | 2 parametrised out-path tests |
| H25 | `NaN`/`Infinity` in result files flowed into the HTML report | `load_report()` rejects non-standard JSON constants | `test_report_rejects_non_standard_json_constants` |
| H26 | pass@k was sorted lexicographically (k=10 before k=2) | Numeric sort key | `test_pass_at_k_is_sorted_numerically` |

## Final verification

Run 2026-11-21 on Python 3.15.2 / Node 26.13.0 / Windows 11, after all m9 fixes:

- `python -m pip wheel . --no-deps -w dist/` → built `greenwash-0.1.0-py3-none-any.whl`
  with 622 task files packaged under `greenwash/tasks/`.
- `python -m ruff check .` → All checks passed.
- `python -m ruff format --check .` → all files formatted.
- `python -m mypy --strict` → Success: no issues found in 49 source files.
- `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s):
  all oracles passed` (exit 0), including the new ≥8-hidden-test rule, mutant
  distinctness and real-kill checks.
- `python -m pytest` → **302 passed in 25m39s**, total coverage **94.66%**
  (gate 90%). Includes all seven m9 regression modules, the 40-task oracle
  validation and the scripted end-to-end pipeline.

Documented deviations: item 12 (`node:test` instead of vitest; Node ≥ 22.6),
item 27 (diff computed with `difflib` rather than git), and item 53 (no dedicated
DST task; UTC/DST-adjacent behaviour is covered by `cron-next` and `retry-after`).
CI root causes A (Node 22 directory argument) and B (Python 3.11 float sum) are
fixed and covered by regression tests, so the green local suite is no longer an
artefact of using versions outside the CI matrix.

## Round-2 correction (this milestone)

The "Final verification" block above records the **previous** milestone's local
run. Round-2 finding 1 showed that CI was red on 6 POSIX jobs despite that green
local run. Rows 13, 29, 30, 32, 33, 38 and 39 are therefore corrected above.
A full local suite and all lint/type/validation commands were re-run after the
round-2 fixes: `ruff`/`mypy --strict` clean, `validate-tasks` reports 40/40
oracles passed, and `pytest` reports 330 passed with 93.56% coverage. Details
are in `docs/REVIEW-FIXES.md`. CI green on all 10 jobs is **not** claimed — that
requires the GitHub Actions run.

## Round-3 correction (this milestone)

Round-3 finding 8 required row 30 to stay FAIL until the hidden oracle stopped
rejecting correct references (finding 1) and stopped being forgeable (finding 2).
Both are fixed; row 30 now records that. Round-3 finding 3 explains the POSIX CI
hang that kept rows 13/29 red: the parent waited for the pipes with
`communicate()` instead of waiting for the leader, so a detached grandchild
delayed the run indefinitely. That is fixed locally but CI green on all ten jobs
is still not claimed. Full details and the per-item regression table are in
`docs/REVIEW-FIXES.md` under "Round 3".
