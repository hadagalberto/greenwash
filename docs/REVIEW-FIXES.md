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
