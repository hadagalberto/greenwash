# Contributing

## Development setup

```sh
python -m pip install -e ".[dev]"
python -m pip wheel . --no-deps -w dist/
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict
python -m pytest
python -m greenwash validate-tasks --tasks tasks
```

These are exactly the commands the GitHub Actions harness job runs on
ubuntu, windows and macos. To try the CLI without an API key, use the committed
scripted-agent example:

```sh
greenwash run --agent scripted --script examples/honest-crc32.json \
  --tasks tasks --glob crc32-check --out results/
```

Line endings are **LF** everywhere (enforced by `.gitattributes`). Do not commit
generated data, virtualenvs or `node_modules`. Commit locally with conventional
commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`). Never push.

## Task authoring guide

A task is a self-contained directory `tasks/<id>/` (lowercase kebab-case `id`,
matching the directory name):

```text
tasks/<id>/
  task.yaml            # metadata and test commands
  spec.md              # the ONLY description the agent receives
  workspace/           # starting repo: skeleton + visible tests
    tests/visible/     # visible tests live here (exact directory name)
  hidden/              # hidden tests; overlay copied at grading time
    tests/hidden/      # hidden tests live here (exact directory name)
  reference/           # correct solution; overlay copied over workspace
  traps/               # >= 2 plausible wrong solutions
  mutants/             # >= 3 one-line mutations of the reference
```

### `task.yaml`

```yaml
id: my-task
title: Human readable title
language: python          # python | typescript
category: parsing         # parsing, numeric, dates/time, money, concurrency,
                          # security, data structures, algorithms, text/i18n, ...
difficulty: easy          # easy | medium | hard
time_budget_s: 120        # default per-command timeout
test_commands:
  visible: python -m pytest -q tests/visible
  hidden: python -m pytest -q tests/hidden
sources:
  - https://www.rfc-editor.org/rfc/rfc4648.txt
protected_files: []       # optional; documented, not enforced (tamper is measured)
```

Unknown top-level keys, missing keys, wrong types, empty strings and an `id` that
does not match the directory are all rejected by the loader. The token `python`
at the start of a command is replaced by the interpreter running greenwash, which
keeps commands portable across virtualenvs.

### Rules for a good task

- `spec.md` must be precise, unambiguous, include examples, and contain **no
  `TODO`**. When the domain has an authoritative source (RFC, ISO, official
  algorithm page), cite it in the spec and in test comments. Fetch the source
  with your own tooling — never invent check values, layouts or rules.
- Visible tests are correct but **incomplete**: they must pass on at least one
  known wrong solution (the traps). They are not a weakened version of the
  hidden suite; they simply cover less.
- Hidden expected values are written by hand or taken from official vectors.
  Hidden tests must **never import from `reference/`** — `validate-tasks`
  checks this statically.
- Each trap is a mistake an LLM plausibly makes (off-by-one, wrong rounding mode,
  swapped alphabet character, ignored pre-release, etc.). It must pass **all**
  visible tests and fail **at least one** hidden test.
- Each mutant is a small mutation of the reference. Hidden tests must kill it
  (at least one hidden failure).
- The reference overlay passes both visible and hidden tests.
- Test code must use real assertions with known-valid and known-invalid vectors;
  no skipped or placeholder tests.

### Test runner conventions

- Python tasks: pytest, tests under `tests/visible/` and `tests/hidden/`,
  module import root is the workspace root (the harness sets `PYTHONPATH`).
- TypeScript tasks: tests under `tests/visible/` / `tests/hidden/` using
  `node:test` and `node:assert/strict`; commands start with `node --test`.
  The full suite may use vitest, but fixture tasks stay dependency-free.
  `node:test` is Stable since Node 20 and `node --test` is the documented CLI
  invocation: https://nodejs.org/api/test.html (fetched 2026-11-20).

A visible test file that the agent skips, empties, deletes or rewrites is
detected as tampering by the git-diff analysis, so keep visible tests meaningful.

### Verification

```sh
python -m greenwash validate-tasks --tasks tasks
```

The command exits non-zero on any violation and prints one line per problem.
