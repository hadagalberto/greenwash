# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
