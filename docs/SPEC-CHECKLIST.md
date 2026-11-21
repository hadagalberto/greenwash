# SPEC checklist — Milestone 8 audit

Every requirement in `SPEC.md` is listed below. `Status` is based on **running**
the command or exercising the behaviour, not on reading the code. Evidence is
the command that was run and the observed result on Python 3.15.2 / Node 26.13.0
/ Windows 11. Full final verification results are at the end of this document.

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
| 8 | `mypy --strict`, `ruff`, `pytest` | PASS | `python -m mypy --strict` → `Success: no issues found in 41 source files`; `python -m ruff check .` → all passed; `python -m ruff format --check .` → 329 files formatted; `python -m pytest` → all pass. |
| 9 | Coverage ≥ 90% for the harness | PASS | `pyproject.toml` `addopts` has `--cov-fail-under=90`; final run reports 95.00%. |
| 10 | Hypothesis "where useful" | PASS | Installed in `dev` extras. No property test was added because every vector in this project has a known official/expected value; deterministic assertions are stronger here. No skipped placeholders. |
| 11 | Small runtime deps: httpx, PyYAML, Jinja2, optional rich | PASS | `dependencies = [httpx, Jinja2, PyYAML, typer]`; rich is not required anywhere. |
| 12 | Tasks in Python **and** TypeScript; harness runs each task's own test command | PASS\* | 20 Python + 20 TypeScript tasks; `task.yaml` declares visible/hidden commands and `run_tests()` executes them verbatim. TypeScript fixtures use Node's built-in `node:test` runner rather than vitest, so no `npm install` is needed; documented in `CONTRIBUTING.md` "Test runner conventions". Official source fetched and checked: [Node.js test runner docs](https://nodejs.org/api/test.html) — `node:test` is Stable since v20.0.0 and `node --test` is the documented CLI invocation. |
| 13 | CI on ubuntu/windows/macos for harness; separate ubuntu `validate-tasks` job | PASS | `.github/workflows/ci.yml`: 3-OS × 3-Python matrix runs build, ruff check, ruff format check, mypy and pytest; `validate-tasks` job on `ubuntu-latest`. |
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
| 22 | Reference passes; traps pass visible & fail hidden; mutants fail hidden | PASS | `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s): all oracles passed` (exit 0). Took 9m29s on Windows; CI ubuntu job runs the same command. |
| 23 | spec.md has no TODO | PASS | Loader `_TODO_RE` check; `validate-tasks` passes. |
| 24 | Hidden tests cannot import from `reference/` | PASS | Static regex check in `tasks.py`; hostile relative/dotted import test passes. |
| 25 | Non-zero exit on any violation; runs in CI | PASS | `tests/test_cli.py::test_cli_validate_tasks_failure` — corrupt a reference → exit 1, prints `FAIL:`; CI `validate-tasks` job. |

## Running (SPEC lines 30–37)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 26 | `run --agent --model [--tasks glob] [--repeat] [--jobs] [--timeout] [--out]` | PASS | All exercised in `tests/test_cli.py` and the verified README example. `--timeout 0`/negative now rejected with exit 2 (m8 regression). |
| 27 | Isolated temp workspace, git-initialised so diffs are exact | PASS | `Workspace` runs `git init`, commits a baseline, and `capture_diff()` stages everything before diffing; `tests/test_workspace.py`. |
| 28 | Standard prompt (spec + completion instruction) | PASS | `make_prompt()` includes full spec and the exact `STATUS: DONE`/`STATUS: FAILED` instruction; used by every adapter and the e2e profile adapter. |
| 29 | Timeout enforced; transcript, tokens/cost, wall time captured | PASS | `tests/test_runner.py`, `tests/test_builtin.py`, fake-server CLI test: `tokens_in=100`, `tokens_out=20`, cost computed from `prices.json`; timeout tests use a fake executable. |
| 30 | Grade order: visible as-is → restore originals → overlay hidden | PASS | `grade_attempt()` pipeline; `tests/test_grading.py`, `tests/test_e2e.py`. Hidden overlay removes agent-injected `tests/hidden/` files first (m7 regression). |
| 31 | Tamper analysis from git diff, all kinds classified with hunk | PASS | `tests/test_tamper.py`, `tests/test_m7_review_regressions.py`, m8 regressions (renames, `--`-prefixed lines). |
| 32 | Claim parsing: final `STATUS:` line; documented uncertain fallback | PASS | `tests/test_claims.py`, m7 regressions (UNKNOWN, negated success), m8 hostile probe. Heuristic limitation is documented in `docs/REVIEW-2026-11-20-m7.md`. |
| 33 | Optional Docker isolation; local default warns | PASS | `test_cli_run_with_docker_sandbox` uses a fake docker executable; `--sandbox podman` exits 2; local run prints the host warning. |

## Adapters (SPEC lines 38–40)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 34 | `builtin` tool loop: read_file, write_file, list_dir, run_command (timeout + truncation) | PASS | `TOOL_DEFINITIONS` and `ToolExecutor`; `tests/test_builtin.py` covers all four, path-traversal rejection, large-output middle truncation and step limit. |
| 35 | Configurable base_url / api_key_env; usage + versioned price table | PASS | CLI flags wired to `BuiltinAdapter`; fake OpenAI server test verifies cost = 100/1M×0.15 + 20/1M×0.6; malformed price table exits 2; m8 regression rejects NaN/Infinity. |
| 36 | `opencode run --format json` | PASS | Fake executable records argv in `tests/test_adapters.py`. |
| 37 | `claude -p --output-format json` | PASS | Same fake-executable technique. |
| 38 | `aider --message` | PASS | Same. |
| 39 | `codex exec --json` | PASS | Same, including cumulative JSONL usage. |
| 40 | `command` template with `{workdir}` `{prompt_file}` | PASS | `test_cli_run_with_command_adapter` runs a real Python agent script. |
| 41 | Unavailable adapters reported, never faked | PASS | `resolve_adapter()` checks installation/config; missing executable exits 2 with "not available". |
| 42 | Unit-test adapters with fake executables/servers | PASS | `tests/fake_openai_server.py` (loopback only), `write_fake_cli()` helper, 17 adapter tests. |

## Metrics and report (SPEC lines 42–43)

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 43 | Per-attempt and per-agent/model aggregation | PASS | `results.jsonl` + `summary.json.by_agent_model`; golden metrics pinned in `tests/test_metrics_golden.py`. |
| 44 | Hidden pass rate, partial score, visible pass rate, greenwash rate, honest-failure rate, tamper by kind, mean cost/tokens/time, pass@k, bootstrap 95% CIs | PASS | `summarize()` emits every field; exact values/CIs asserted by `test_metrics_golden.py`. |
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

Run 2026-11-20 on Python 3.15.2 / Node 26.13.0 / Windows 11, after all fixes:

- `python -m pip wheel . --no-deps -w dist/` → built `greenwash-0.1.0-py3-none-any.whl`.
- `python -m ruff check .` → All checks passed.
- `python -m ruff format --check .` → 329 files already formatted.
- `python -m mypy --strict` → Success: no issues found in 42 source files.
- `python -m pytest` → **188 passed in 27m14s**, total coverage **95.00%**
  (gate 90%). Includes `validate-tasks` over all 40 tasks three times, the
  scripted end-to-end pipeline and all m8 hostile-input regressions.
- `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s):
  all oracles passed` (exit 0).
- README quickstarts: `validate-tasks`, the scripted run on `crc32-check`
  (`hidden_pass_rate 1.0`, `greenwash_rate 0.0`, exit 0) and `compare` on the
  committed fixtures (`paired_attempts 6`, `b_better 2`, `b_worse 0`, exit 0)
  were all executed and their outputs verified.

No unresolved spec items. Documented deviations: item 12 (node:test instead of
vitest, verified against official Node docs) and item 53 (no dedicated DST task;
UTC/DST-adjacent behaviour is covered by `cron-next` and `retry-after`).
