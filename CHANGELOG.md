# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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
