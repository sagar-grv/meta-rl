# Conservative Judge-Round Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve hidden-case robustness and anti-shortcut reliability with minimal-risk changes while preserving current Phase 2 passing behavior.

**Architecture:** Add conservative robustness tests and audit scenarios first, then make the smallest reward/policy adjustments needed to satisfy those tests. Keep API contract, determinism, and strict score open-interval behavior unchanged. Validate through one clean end-to-end preflight run before deployment.

**Tech Stack:** Python 3.11, pytest, FastAPI/OpenEnv environment, local audit/probe scripts.

---

### Task 1: Baseline Freeze and Safety Snapshot

**Files:**
- Modify: `docs/superpowers/plans/2026-04-09-conservative-judge-round-hardening.md`
- Verify only: `tests/`, `scripts/judging_audit.py`, `scripts/probe_endpoints.py`

- [ ] **Step 1: Run full baseline tests**

Run: `set PYTHONPATH=envs;. && .venv\Scripts\python.exe -m pytest -q`
Expected: PASS with current suite count.

- [ ] **Step 2: Run current judging audit**

Run: `set PYTHONPATH=envs;. && .venv\Scripts\python.exe scripts\judging_audit.py`
Expected: all checks PASS.

- [ ] **Step 3: Record baseline metrics in notes**

Record: key averages from policy ordering and any current shortcut scores from output.

- [ ] **Step 4: Commit (optional checkpoint)**

Run:
`git add docs/superpowers/plans/2026-04-09-conservative-judge-round-hardening.md`
`git commit -m "docs: add conservative judge-round hardening plan"`

### Task 2: Add Failing Judge-Like Tests (TDD RED)

**Files:**
- Modify: `tests/test_environment_contract.py`
- Modify: `tests/test_inference_policy.py`

- [ ] **Step 1: Add one failing environment robustness test**

Add a test for borderline escalation cue phrasing that should prefer contextual escalation response over generic support response.

- [ ] **Step 2: Add one failing inference robustness test**

Add a test that template-reuse output across distinct tasks should be less preferred than task-aware output.

- [ ] **Step 3: Run only new tests to verify they fail for the right reason**

Run: targeted `pytest -q` with `-k` selectors for new test names.
Expected: FAIL due to current weakness, not syntax/import issues.

- [ ] **Step 4: Commit RED tests (optional checkpoint)**

Run:
`git add tests/test_environment_contract.py tests/test_inference_policy.py`
`git commit -m "test: add conservative judge-round robustness regressions"`

### Task 3: Extend Audit Scenarios (Conservative)

**Files:**
- Modify: `scripts/judging_audit.py`
- Modify: `tests/test_judging_audit.py`

- [ ] **Step 1: Add 2 realistic adversarial policy variants**

Examples: low-context polite generic response; single-template response reused across tasks.

- [ ] **Step 2: Add relative ordering/threshold checks only**

Avoid aggressive absolute constraints that can destabilize valid behavior.

- [ ] **Step 3: Update audit tests if needed**

Ensure expected check names remain present and all checks are expected to pass after implementation.

- [ ] **Step 4: Run audit tests only**

Run: `set PYTHONPATH=envs;. && .venv\Scripts\python.exe -m pytest -q tests/test_judging_audit.py`
Expected: PASS.

### Task 4: Minimal Reward/Policy Hardening (TDD GREEN)

**Files:**
- Modify: `envs/support_queue_env/server/your_environment.py`
- Modify (only if tests prove required): `inference.py`

- [ ] **Step 1: Patch minimal scoring logic**

Adjust only the narrow terms required by failing tests (for example context/relevance weighting vs template penalties).

- [ ] **Step 2: Run targeted previously failing tests**

Run: targeted `pytest -q` selectors for new tests.
Expected: PASS.

- [ ] **Step 3: Run nearby regression tests**

Run: `test_environment_contract.py`, `test_inference_policy.py`, `test_judging_audit.py`.
Expected: PASS.

- [ ] **Step 4: Commit minimal behavior changes**

Run:
`git add envs/support_queue_env/server/your_environment.py inference.py scripts/judging_audit.py tests/test_environment_contract.py tests/test_inference_policy.py tests/test_judging_audit.py`
`git commit -m "feat: conservative judge-round robustness hardening"`

### Task 5: Strict End-to-End Gate and Deploy Decision

**Files:**
- Verify only: `server/app.py`, `scripts/probe_endpoints.py`, `scripts/submission_pipeline.py`

- [ ] **Step 1: Full tests**

Run: `set PYTHONPATH=envs;. && .venv\Scripts\python.exe -m pytest -q`
Expected: full PASS.

- [ ] **Step 2: Audit and validator**

Run:
`set PYTHONPATH=envs;. && .venv\Scripts\python.exe scripts\judging_audit.py`
`.venv\Scripts\openenv.exe validate`
Expected: audit PASS and OpenEnv ready.

- [ ] **Step 3: Live endpoint probe**

Run local server, then:
`set PYTHONPATH=envs;. && .venv\Scripts\python.exe scripts\probe_endpoints.py --base-url http://127.0.0.1:7860`
Expected: zero failures.

- [ ] **Step 4: Inference smoke**

Run with env vars:
`set PYTHONPATH=envs;.`
`set MODEL_NAME=gpt-test`
`set API_BASE_URL=https://router.huggingface.co/v1`
`set HF_TOKEN=dummy`
` .venv\Scripts\python.exe inference.py`
Expected: strict START/STEP/END output and clean completion.

- [ ] **Step 5: Deploy only if one clean run passes all gates**

Run:
`git push origin main`
`git push hf main`

- [ ] **Step 6: Capture final evidence**

Record commit hash, gate summary, and whether robustness metrics improved vs baseline.
