# Local Submission Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-only submission pipeline that runs all pre-submit checks before every submission and turns pasted dashboard output into concrete next-step improvements and regression cases for the next run.

**Architecture:** Keep the existing environment, baseline, and validator checks as the source of truth, then add one small local CLI layer that orchestrates those checks and one analyzer that parses dashboard text into categorized failures, suggested fixes, and new edge cases. The preflight path should fail fast and be reproducible; the dashboard-analysis path should be text-driven, deterministic, and easy to extend with new failure patterns.

**Tech Stack:** Python 3.11, subprocess, argparse, pytest, OpenEnv validator, the existing local HTTP probe, the existing support queue environment, Markdown/text parsing, and the current OpenAI-client baseline script.

---

### Task 1: Add a local submission pipeline CLI

**Files:**
- Create: `scripts/submission_pipeline.py`
- Create: `tests/test_submission_pipeline.py`

- [ ] **Step 1: Write failing tests for the pipeline entry points**
  - Add tests for a `parse_dashboard_report()` helper that classifies pasted dashboard text into the known failure buckets.
  - Add tests for a `build_preflight_steps()` or equivalent helper that returns the exact local checks in execution order.
  - Add tests for a `build_next_submission_actions()` helper that maps one or more findings to a fix list and new regression cases.

- [ ] **Step 2: Run the new tests and confirm they fail**
  - Run: `pytest tests/test_submission_pipeline.py -v`
  - Expected: import or symbol failures before implementation exists.

- [ ] **Step 3: Implement the minimal pipeline logic**
  - Add a small CLI with `preflight` and `analyze-dashboard` commands.
  - Make `preflight` run local validation gates in order: pytest, openenv validate, endpoint probe, inference dry-run.
  - Make `analyze-dashboard` accept pasted text or a file path and emit a categorized report with suggested fixes and new edge-case tests.

- [ ] **Step 4: Re-run the tests and confirm they pass**
  - Run: `pytest tests/test_submission_pipeline.py -v`
  - Expected: PASS.

- [ ] **Step 5: Commit the pipeline CLI**
  - Commit message should mention local preflight and dashboard analysis.

### Task 2: Add dashboard failure classification and regression suggestions

**Files:**
- Modify: `scripts/submission_pipeline.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing tests for failure classification rules**
  - Cover at least these classes: score-range violation, determinism/variance issue, endpoint contract failure, logging format failure, deployment/runtime failure, and generic quality regression.
  - Add adversarial shortcut cases such as always-one-route, keyword stuffing, empty response, and overlong irrelevant response.

- [ ] **Step 2: Implement the classification and suggestion rules**
  - Use deterministic keyword rules so the same dashboard text always maps to the same category.
  - Return a short list of exact next actions: targeted fix, test file to add or modify, and the next local gates to rerun.

- [ ] **Step 3: Re-run the tests and confirm the classification is stable**
  - Run: `pytest tests/test_submission_pipeline.py -v`
  - Expected: PASS with the new failure cases.

- [ ] **Step 4: Update documentation**
  - Document the local workflow in `README.md` with two commands: preflight and dashboard analysis.
  - Show how to paste dashboard output into a local text file or pipe it into the analyzer.

### Task 3: Add a strict pre-submit runbook

**Files:**
- Modify: `README.md`
- Modify: `scripts/validate-submission.sh`

- [ ] **Step 1: Write failing documentation/test expectations**
  - Add a test that asserts the preflight step list includes the current local gates in the correct order.
  - Confirm the validator wrapper mentions the new local pipeline command.

- [ ] **Step 2: Wire the runbook into the existing submission flow**
  - Keep the existing validator wrapper intact, but point the README to the new preflight command as the preferred local gate.
  - Ensure the pipeline can be run against a local server and against a pasted dashboard report without needing remote log scraping.

- [ ] **Step 3: Re-run the full test suite**
  - Run: `pytest -q`
  - Expected: PASS.

- [ ] **Step 4: Commit the runbook update**
  - Commit the updated documentation and script changes together.

**Relevant files**
- `scripts/submission_pipeline.py` — new local CLI for preflight and dashboard analysis.
- `tests/test_submission_pipeline.py` — tests for classification, preflight ordering, and regression suggestions.
- `README.md` — local usage instructions and runbook.
- `scripts/validate-submission.sh` — existing validator wrapper, optionally referenced by the new pipeline.
- `scripts/probe_endpoints.py` — existing evaluator-like endpoint probe reused by preflight.
- `inference.py` — current baseline runtime and structured log contract.
- `envs/support_queue_env/server/your_environment.py` — current reward logic and deterministic environment behavior.
- `tests/test_inference_contract.py` — current logging-format regression coverage.
- `tests/test_inference_policy.py` — current policy robustness coverage.

**Verification**
1. `pytest tests/test_submission_pipeline.py -v`
2. `pytest -q`
3. `python scripts/submission_pipeline.py preflight --base-url http://127.0.0.1:7861`
4. `python scripts/submission_pipeline.py analyze-dashboard --input dashboard.txt`
5. Confirm every dashboard failure maps to a concrete next action and at least one new regression case when appropriate.

**Decisions**
- The pipeline stays local-only and text-driven; no direct GitHub or HF log scraping is required.
- Dashboard text is treated as the authoritative post-submission input because that is what you can reliably provide in this workspace.
- The pipeline should be deterministic, low-maintenance, and fail-fast.

**Further Considerations**
1. Add a single Markdown report output file if you want to archive each submission analysis locally.
2. Add GitHub Actions later if you decide to automate pre-submit checks in CI.
3. Add a small case library so dashboard failures automatically append new probe cases over time.
