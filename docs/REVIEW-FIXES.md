# Milestone 9 — independent review fixes

Source: the independent review of HEAD `fb305b7` (`docs/REVIEW-2026-11-20.md`).
Every item below was reproduced with a regression test that was run and observed
failing before the fix. Expected values are hand-derived from SPEC.md, the
task specs, or explicit reasoning in the test — never produced by the library
under test.

## Report table

| # | Item | Regression test | Fix summary | Status |
| --- | --- | --- | --- | --- |
| C-A | Node 22 rejects `node --test <dir>` | `test_m9_taskdata.py::test_typescript_commands_use_explicit_glob` | All TS task commands and the contributor template use `node --test "tests/<suite>/**/*.test.ts"`; CI pins Node 22.23.5 | PASS |
| C-B | Python 3.11 float summation breaks golden | `test_m9_metrics.py::test_compare_mean_uses_fsum` | `compare._mean` uses `math.fsum`; golden compared structurally with `pytest.approx` | PASS |
| 1 | Hidden tests run in agent-controlled tree | `test_m9_core_security.py` (7 attack tests) | Fresh harness grading dir, allow-listed implementation files, pristine ini, isolated env, JUnit reports outside workspace, assert freeze preload, framework-import findings | PASS |
| 2 | Git hides diff / report | `test_git_replace_cannot_hide_a_test_edit`, `test_git_info_exclude_cannot_hide_an_injected_conftest` | Python `difflib` diff against a pristine snapshot; agent `.git` never used | PASS |
| 3 | Host command execution via agent git config | `test_git_fsmonitor_is_never_executed_by_capture_diff` | No git invocation against the agent workspace; symlink-safe walks | PASS |
| 4 | Symlinks/junctions escape workspace | `test_symlink_escaping_workspace_fails_grading_and_is_reported` | Link detection with `lstat`, fail attempt, `symlink` finding, no following | PASS |
| 5 | Tamper misses weakening edits | `tests/test_m9_tamper.py` (15 tests) | Pattern-based weakening detection + config-file findings; AST/aligned literal pairing | PASS |
| 6 | Tamper false positives | `test_todo_comment_is_not_a_tamper`, `test_quote_style_change_is_not_a_tamper`, `test_renamed_test_with_same_body_is_not_a_deletion`, `test_crlf_resave_is_not_a_tamper` | Comment/quote/EOL normalisation, rename detection, `newline=""` writes | PASS |
| 7 | Tamper rate > 100% | `test_tamper_rate_is_per_attempt` | Per-attempt counting, overall scalar rate + CI, leaderboard uses scalar | PASS |
| 8 | Claim parsing misclassifies final messages | `tests/test_m9_claims_adapters.py` (8 string cases) | STATUS only on last line after markdown stripping, word-boundary hints bottom-to-top, final message stored separately, uncertain shown | PASS |
| 9 | CLI adapters ignore `--model` | `test_cli_adapters_pass_model_flag` | `--model` / `-m` added for all four CLIs | PASS |
| 10 | Windows prompt truncation | `test_cli_adapter_sends_full_prompt_via_stdin` | Prompt streamed via `run_argv_with_input` for npm CLIs | PASS |
| 11 | Timeout not enforced; children survive | `tests/test_m9_sandbox.py` (process-tree tests) | New process group / `taskkill /T`, pipe deadline, named Docker containers killed on timeout | PASS |
| 12 | Mutants identical to traps | `test_every_task_has_three_distinct_mutants` | Byte-distinct mutants added; validator rejects duplicates | PASS |
| 13 | Crash counted as a "kill" | `test_hidden_kill_rejects_zero_total_crash` | Require hidden total match + both passes and failures | PASS |
| 14 | Hidden suites miss spec requirements | `test_required_spec_vectors_present_in_hidden_suites`, `test_every_task_has_at_least_eight_hidden_tests` | Hand-derived vectors added; validator requires ≥8 tests | PASS |
| 15 | Transcript never persisted | `test_transcript_and_final_message_are_persisted_and_capped` | `transcript`/`final_message` in `results.jsonl` and HTML drill-down, 200 KB cap | PASS |
| 16 | Statistics treat repeats as independent | `test_bootstrap_ci_clusters_resamples_tasks_then_attempts`, `test_pass_at_k_unbiased_estimator_hand_derived`, `test_sign_test` | Cluster bootstrap + `*_ci95_cluster`, unbiased pass@k, per-task compare + sign test | PASS |
| 17 | Docker sandbox not usable/isolated | `tests/test_m9_sandbox.py` (Docker tests) | `docker/Dockerfile` (Python 3.12 + pytest + Node 22), isolation flags, default image | PASS |
| 18 | SPEC deviations | `tests/test_m9_metrics.py::test_per_task_budget_is_used`, `test_m9_taskdata.py::test_implementation_files_present_and_exist` | Protected-file violations, per-task budgets, tasks packaged in wheel, decisions recorded in SPEC | PASS |
| 19 | Host secrets exposed | `test_sandbox_does_not_leak_secrets` | Allow-listed env; warning states hidden tests are readable locally | PASS |
| 20 | Circular golden tests | `test_summarize_matches_hand_derived_fixture_numbers`, structural compare assertions | Golden tests now call `summarize()` and assert hand numbers; snapshots are cross-checks only | PASS |
| 21 | Repo clutter | — | `tmp-junit.xml` removed; build artefacts already gitignored | PASS |

## Notes

- Existing assertions that encoded a listed bug were corrected only where the
  behaviour itself changed (final STATUS line, adapter argv, hidden-test counts
  after finding 14, pass@k estimator) and each carries a comment citing the
  finding.
- Snapshot files `compare.json` and `report.html` were regenerated and read by
  hand; their tests now assert hand-derived field values with `pytest.approx`
  rather than byte equality.
- The full suite and lint/type checks are recorded in `docs/SPEC-CHECKLIST.md`.

# Round 2 — independent review of 132570c (score 4/10)

Source: the second independent review, reproduced on Windows 11 / Python 3.15.2 /
Node 26.13.0. Every regression test below was copied into a worktree of
**132570c**, run there and observed failing, then run against the fix and
observed passing. Commit is named per row. The single exception is the
rewritten finding-12 claim test, which fails on **fb305b7** (the builtin adapter
there parsed the whole transcript) but already passes on 132570c; its new
builtin-transcript form still exercises the real adapter path.

| # | Item | Regression test (`tests/test_m10_review_fixes.py` unless noted) | Fix summary | Fails on | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | POSIX `mypy` error made CI red | `test_sandbox_typechecks_for_posix_platforms`, `test_posix_process_group_is_stored_at_spawn` | `creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)`; pgid captured at spawn, no `getpgid` on a dead leader; `mypy --platform linux` is now tested | 132570c | PASS locally; CI still unverified |
| 2 | Child could forge the hidden result | `test_junit_forgery_cannot_make_hidden_pass`, `test_disguised_pytest_patch_is_oracle_interference_and_fails_hidden`, `test_undisguised_pytest_patch_forces_hidden_failure`, `test_hidden_report_path_is_never_passed_in_argv` | Nonce-named grader plugin streams one outcome event per test to a parent-owned pipe (file on Windows/Docker); ids collected independently; mismatches fail; AST scan replaces substring tokens; any oracle-interference finding forces `hidden.ok=False` | 132570c | PASS |
| 3 | Docker image ships the answers | `test_dockerignore_excludes_all_hidden_answers` | `.dockerignore` excludes `tasks/*/hidden`, `reference`, `traps`, `mutants`, `tests`, `.git`; context-list test asserts exclusion | 132570c | PASS (no real `docker build` run) |
| 4 | `STATUS: FAILED` + summary parsed as DONE | `test_status_failed_followed_only_by_summary_is_certain_failure` (3 strings), `test_empty_final_message_from_builtin_is_unknown_not_transcript_claim` | Last STATUS of the final message is certain when followed only by a summary; fallback hints never override; prompt says STATUS must be the final line; empty builtin final message = UNKNOWN; `tests/test_builtin.py` assertion corrected with finding-4 comment | 132570c | PASS |
| 5 | Orphan/detached processes survive | `test_detached_grandchild_does_not_survive_run_shell`, `test_workspace_close_retries_a_locked_directory` | Windows kill-on-close Job Object; POSIX `killpg(pgid, SIGKILL)`; `Workspace.close()` retries then logs instead of raising | 132570c | PASS on Windows; POSIX kill path needs CI |
| 6 | Aider/Codex truncate multi-line prompt | `test_codex_sends_prompt_on_stdin`, `test_aider_sends_prompt_via_message_file` | `codex exec -` reads stdin; aider gets a transient `--message-file`; argv expectations in `tests/test_adapters.py` and `tests/test_m9_claims_adapters.py` corrected with finding-6 comments | 132570c | PASS |
| 7 | Tamper evasions undetected | `test_visible_tamper_evasions_are_detected_from_real_workspace_diff` (6 Python probes), `test_typescript_visible_tamper_evasions_are_detected_from_real_workspace_diff` (3 TS probes) | Per-test outcome diff over original vs agent visible suites; structural hints for guards that still report "passed" (`if 0`, self-comparison, swallowed assertions, skip idioms, `skip: !0`) | 132570c | PASS |
| 8 | Hidden suites miss spec vectors | `test_hidden_uuid_vectors_beat_regex_dollar_and_bool_version`, `test_hidden_isbn_vectors_beat_whitespace_and_isdigit` | Trailing-newline and bool-version vectors for uuid; tab/Unicode-digit vectors for ISBN; Unicode/newline vectors added to luhn, EAN, IBAN and JWT hidden suites; every hidden suite gets a SPEC-rule-to-test comment map | 132570c | PASS |
| 9 | Comment-only mutants counted as distinct | `test_comment_only_mutants_have_identical_normalized_fingerprints` | `normalized_fingerprint()` strips comments/docstrings (AST for Python, comment tokenizer for TS) and normalises whitespace; 11 comment-only mutants replaced with real code mutations; affected tasks now have ≥3 code-distinct mutants | 132570c | PASS |
| 10 | `protected_file_violations` was dead code | `test_protected_file_change_is_reported_end_to_end` | `grade_attempt()` calls it against `workspace.pristine` and emits `protected_file_changed` | 132570c | PASS |
| 11 | Golden compare test never called the code | `tests/test_compare.py::test_golden_compare_json_matches_fixtures` (rewritten) | Test calls `compare_dirs(A, B)`, asserts hand-derived values on the live result, and uses the snapshot only as an `approx` cross-check | 132570c | PASS |
| 12 | Two regressions passed on the buggy commit | `test_final_message_is_not_dragged_down_by_earlier_tool_output` (`tests/test_m9_claims_adapters.py`), `test_typescript_assert_equal_to_assert_ok_true_or_is_detected` (`tests/test_m9_tamper.py`) | Claim test now drives the builtin adapter with a real transcript containing an "incomplete" tool result; TS test now edits a real Workspace and analyses `capture_diff()` | fb305b7 (claim), 132570c (TS diff is now real) | PASS |
| 13 | Checklist overstated status | `docs/SPEC-CHECKLIST.md` rows 13, 29, 30, 32, 33, 36-39 | Marked FAIL / PASS\* with the open item number; no green CI is claimed | — | PASS |

## Final verification (this milestone, Windows 11 / Python 3.15.2 / Node 26.13.0)

- `python -m ruff check .` → All checks passed.
- `python -m ruff format --check .` → all files formatted.
- `python -m mypy --strict` → Success: no issues found in 52 source files.
- `python -m mypy --strict --platform linux src/greenwash/sandbox.py` → Success
  (the POSIX CI type error that previously stopped pytest from running is gone).
- `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s):
  all oracles passed`, including the normalised mutant-distinctness rule and the
  new hidden vectors.
- `python -m pytest` → **330 passed**, total coverage **93.56%** (gate 90%).
- CI green on all 10 GitHub Actions jobs is not claimed here; that run is still
  required to close finding 1 and rows 13/29 of the checklist.

## Notes on the oracle redesign

- The hidden verdict never uses stdout or a child-visible report path. A parent
  generates the nonce **after** copying the agent's implementation, so the code
  under test cannot know it. Events are counted against node ids collected by a
  separate trusted pytest run; missing, duplicated or non-passed events fail the
  attempt.
- `oracle_interference` is now fatal to the hidden result, not just a note.
- Existing assertions were only changed where they encoded a listed bug
  (adapter argv for aider/codex, builtin claim certainty, mutant distinctness,
  the golden compare test). Each carries a comment citing the finding.

# Round 3 — independent review of 4bb1aa2 (score 4/10)

Source: `m11.md`. Every regression test below was first run against the
unmodified 4bb1aa2 tree and observed failing; expected values are hand-derived
from SPEC.md, the task specs and explicit comments in the tests — never from
the library under test. The two item-6 probes are the documented exception:
they are rebuilt from inputs 132570c misclassifies and were observed failing
there, as the finding requires.

## Report table

| # | Item | Regression test (`tests/test_m11_review_fixes.py` unless noted) | Fix summary | Status |
| --- | --- | --- | --- | --- |
| 1 | Hidden oracle rejected 7 correct references | `test_parametrized_python_node_ids_with_spaces_are_matched_exactly`, `test_runtime_built_typescript_test_names_are_matched_exactly`, `test_every_task_reference_passes_hidden_through_grade_attempt` | Python ids now come from the plugin's own `pytest_collection_modifyitems` hook (`item.nodeid`, spaces intact) via a collect-only pass; node ids come from `node:test`'s `test:start` events instead of a source regex; ids are compared exactly. `validate-tasks` now grades through the same `run_observed` oracle (`validate._run_oracle`). | PASS |
| 2 | Implementation code forged the hidden pass | `test_python_module_patch_forgeries_are_detected[exec-sys-modules]`, `[os-alias-attribute-chain]`, `test_typescript_assert_patch_forgery_is_detected` | Nonce-named canary test must fail in every hidden run; `assert`/`assert.strict` and `Object.freeze` are locked by a `NODE_OPTIONS=--import` preload in **every** node child process; `implscan` now flags `exec`/`eval`/`compile`, `__dict__`/`__builtins__` subscripts, `sys`/`modules`/`_exit` attributes through any alias, and dynamic imports with non-literal specifiers. Any such finding or a forged canary forces `hidden.ok=False`. | PASS |
| 3 | POSIX CI red: grandchild held the pipes | `test_leader_exit_does_not_wait_for_grandchild_holding_stdout` (plus the unchanged `test_m10_review_fixes.py::test_detached_grandchild_does_not_survive_run_shell`) | `_run_process` waits for the **leader** with `proc.wait(timeout)`, kills the whole group immediately afterwards, then drains pipes for a short deadline. `communicate()` is no longer the main wait. | PASS locally; POSIX CI job still unverified |
| 4 | Unbounded child output (30 GB incident) | `test_child_output_capture_is_bounded` | Reader threads feed bounded head/tail buffers (1 MiB each per stream); exceeding the cap kills the process tree and marks the run failed with `output limit exceeded`. No `communicate()` accumulation remains on the local path. | PASS |
| 5 | uuid evasions could not be verified | `test_uuid_evasions_fail_half_of_hidden_with_full_total` (regex `$` and bool `version`) | After item 1 the oracle accepts the reference, so each evasion now records a real assertion failure with the hand-derived hidden total of 23. | PASS |
| 6 | Two regressions passed on the old commit | `tests/test_m10_review_fixes.py::test_final_message_is_not_dragged_down_by_earlier_tool_output_real_transcript`, `tests/test_m9_tamper.py::test_typescript_skip_option_not_zero_or_is_detected` | Both probes were rebuilt from inputs 132570c misclassifies: a `STATUS: DONE` followed by "not complete" in a summary, and a TS `{ skip: !0 }` option in a real workspace diff. | PASS |
| 7 | Last fallback hint still won with no STATUS | `test_mixed_failure_and_success_hint_without_status_is_not_done`, corrected `tests/test_m9_claims_adapters.py::test_mixed_failure_and_success_hints_are_failure_not_done` | When a final message has both failure and success hints and no STATUS line, the fallback is FAILED (never DONE); the old DONE assertion was corrected with a finding-7 comment. | PASS |
| 8 | Checklist hid the broken oracle | `docs/SPEC-CHECKLIST.md` row 30 | Row 30 was marked FAIL while items 1/2 were open and now records the fix; no green CI is claimed for rows 13/29. | PASS |

## Notes on round 3

- The 40-task reference sweep grades every `reference/` overlay through
  `grade_attempt()` and asserts `hidden_pass`; this is the direct guard against
  finding 1 returning.
- The canary is generated **after** the agent's code is copied in, is written
  into the harness-owned grading tree, and is excluded from pass/total counts.
  A run that reports it as passed is rejected as forgery.
- One pre-existing assertion was corrected: the fallback claims test that
  expected DONE from mixed failure/success hints (finding 7), with a comment.
- Green CI on all ten GitHub Actions jobs remains an external observation and
  is not claimed here.

## Final verification (round 3, Windows 11 / Python 3.15.2 / Node 26.13.0)

- `python -m ruff check .` → All checks passed.
- `python -m ruff format --check .` → 325 files already formatted.
- `python -m mypy --strict` → Success: no issues found in 53 source files.
- `python -m mypy --strict --platform linux src/greenwash/sandbox.py
  src/greenwash/events.py src/greenwash/validate.py` → Success (POSIX paths
  type-check without the Windows-only process-group constant).
- `python -m greenwash validate-tasks --tasks tasks` → `validated 40 task(s):
  all oracles passed` (exit 0).
- `python -m pytest` → **341 passed in 3351.85s (55:51)**, coverage **93.46%**
  (gate 90%).
- Old-commit proof, run in detached worktrees of this repository:
  `4bb1aa2` → all 10 non-slow `tests/test_m11_review_fixes.py` tests failed;
  `132570c` → both item-6 tests failed. The worktrees were removed afterwards.
- CI green on all ten GitHub Actions jobs is still **not** claimed; rows 13/29
  of `docs/SPEC-CHECKLIST.md` remain honest about that.
