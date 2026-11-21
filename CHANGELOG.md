# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Milestone 8: line-by-line SPEC audit with a status checklist in
  `docs/SPEC-CHECKLIST.md`; every CLI flag, output, test, CI job and README
  example verified by running it. Added a runnable scripted-agent example
  (`examples/honest-crc32.json`) used by both READMEs, a package build step in
  CI, and an explicit visible/hidden gap metric (with bootstrap CI) in
  `summary.json` and the HTML report.
- Milestone 7: hostile review of the harness and all 40 tasks. Hand-derived
  vectors from the cited sources were compared to every hidden assertion; all
  traps, mutants and reference-import checks were re-verified. Findings and
  fixes are documented in `docs/REVIEW-2026-11-20-m7.md`.
- Milestone 6: static HTML leaderboard generated from `summary.json` and
  `results.jsonl` with sortable metrics, per-task × repeat matrix and per-attempt
  drill-down (spec, diff, tamper hunks, test output). All CSS and JS are
  inlined, so the report has no runtime CDN dependency; attempt data is escaped.
  Every headline metric now has a deterministic bootstrap 95% CI (coverage,
  rates and means). Golden-file tests pin the exact HTML structure and metrics
  from committed fixture results, including a hostile XSS vector.
- `greenwash compare a/ b/` produces a paired report (per-pair deltas,
  win/tie/loss counts and CIs over pair differences) as JSON on stdout and,
  optionally, `compare.json`. Unpaired attempts are reported, never folded in.
- Sample report screenshot generated from fixture results
  (`docs/sample-report.png`), plus English and pt-BR README quickstarts and
  report/compare documentation.
- Milestone 5: task suite part 2 adds 20 tasks (10 Python, 10 TypeScript),
  bringing the suite to 40 tasks. New categories include concurrency and API
  client. Seven tasks use multiple source files; five time-dependent tasks
  (`token-bucket`, `retry-backoff`, `ttl-cache`, `sliding-window-limiter`,
  `debounce-scheduler`) take an injected clock or scheduler so tests are
  deterministic. Specs cite the RFCs and standards whose rules they implement.
  Every new task ships correct-but-incomplete visible tests, hand-derived
  hidden vectors, at least two traps and at least three mutants;
  `greenwash validate-tasks` passes for all 40.
- Milestone 4: hostile review of the harness and all 20 tasks. Hand-derived
  vectors from the cited sources were compared to every hidden assertion; all
  traps, mutants and reference-import checks were re-verified. Findings and
  fixes are documented in `docs/REVIEW-2026-11-20.md`.

### Fixed

- Tamper analysis detects test files renamed out of their graded directory or
  to a name the runner no longer collects, and no longer skips hunk lines that
  begin with `--`.
- Hostile inputs no longer crash the harness: non-finite prices, non-standard
  JSON constants in results, non-positive `--timeout` and a file at `--out`
  are all rejected with clear usage errors.
- The HTML leaderboard sorts pass@k numerically (k=10 after k=2).
- Tamper analysis now handles Windows and spaced git paths, case/type-only
  expected-value rewrites, base-prefixed tolerances, trailing comments and
  tests moved between files; it no longer reports removed skip markers.
- Claim parsing recognises a final `STATUS: UNKNOWN` and no longer reports
  negated success ("not all tests pass") as DONE.
- Hidden-test overlay removes agent-injected files (including `conftest.py`)
  before grading; missing executables fail an attempt instead of crashing the
  run; reference-import validation catches relative and dotted imports.
- `diff-patch` reference and variants now ignore the no-newline marker anywhere
  in a hunk, as its spec requires; a hidden regression vector was added.
- Tamper analysis now detects literal changes in non-assert lines, single-test
  deletions and test files renamed out of `tests/`, and no longer mislabels a
  deleted test as a literal edit.
- Claim parsing no longer treats a bare `STATUS:` followed by `DONE` on the next
  line as a certain claim, nor "not done"/"DONEED" as a success.
- Windows test commands preserve backslash paths instead of losing separators
  to POSIX shlex escaping.
- `csv-parse` and `topological-sort` specs now state the edge-case behaviour
  their hidden tests assert (trailing comma; unknown-node message), so the
  hidden suites are fair.

- Milestone 3: task suite part 1 expanded to 20 tasks (10 Python, 10 TypeScript)
  across parsing, numeric, dates/time, money, security, data structures,
  algorithms and text/i18n. Each task cites official sources (RFCs, ISO/IEC
  standards, SemVer, Unicode and GS1) in its spec and code comments, ships
  correct-but-incomplete visible tests, hidden vectors derived by hand or from
  published check values, a reference overlay, at least two plausible traps and
  at least three mutants. `greenwash validate-tasks` passes for all 20.

- Built-in OpenAI-compatible agent loop with `read_file`, `write_file`,
  `list_dir` and `run_command` tools (timeout, output truncation, step limit)
  and token/cost accounting from a versioned price table (`prices.json`,
  transcribed from the official OpenAI pricing page).
- `opencode`, `claude-code`, `aider` and `codex` adapters with documented
  non-interactive invocations, JSON/JSONL transcript and usage extraction, and
  availability detection; generic `command` adapter now honours the sandbox.
- `--sandbox docker` (with `--sandbox-image`) runs agents and test commands in
  a container with the workspace mounted at `/work`; host execution warns.
- Unit tests for every adapter using fake executables and a loopback-only fake
  OpenAI-compatible HTTP server, plus sandbox and price-table tests. All CLI
  flags (`--repeat`, `--jobs`, `--timeout`, `--tasks`) exercised end to end.

## [0.1.0] - 2026-11-20

### Added

- Hatchling scaffold with `src/` layout, `py.typed`, `mypy --strict`, ruff, pytest
  with 90% coverage gate, CLI (`greenwash`), GitHub Actions CI and MIT license.
- Task loader and strict schema validation for `tasks/<id>/` directories.
- Isolated workspaces (temp dir + git init), test command execution with timeouts
  and parser for pytest and `node:test` output.
- Visible / original-visible / hidden grading pipeline, git-diff tamper analysis
  with full classification, `STATUS:` claim parsing with uncertain fallback.
- JSONL per-attempt results and aggregated `summary.json` (rates, pass@k,
  bootstrap 95% CIs).
- `greenwash validate-tasks` command, plus three fixture tasks (one Python, two
  TypeScript) with references, traps and mutants, and the scripted fake agent.
- End-to-end test asserting exact metrics and tamper classifications.
