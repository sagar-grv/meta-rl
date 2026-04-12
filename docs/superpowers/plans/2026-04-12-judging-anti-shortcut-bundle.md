# Judging Anti-Shortcut Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve judging robustness by reducing reward leakage from shortcut replies while preserving the strong contextual behavior already validated on the benchmark tasks.

**Architecture:** Keep the change isolated to the environment reward function in `envs/support_queue_env/server/your_environment.py`. The implementation should tighten penalties for the exact shortcut families that the judging audit already probes: repetitive keyword stuffing, mixed-intent stuffing, and apology-led boilerplate. Existing contract, deterministic behavior, open-interval score clamping, and `inference.py` log formatting must remain unchanged.

**Tech Stack:** Python 3.11, pytest, Pydantic models, FastAPI environment wrapper, OpenEnv submission audit scripts.

---

### Task 1: Lock in failing shortcut regression tests

**Files:**
- Modify: `tests/test_environment_contract.py`
- Modify: `tests/test_inference_policy.py`

- [ ] **Step 1: Write the failing test**

Add or tighten tests that encode the target behavior for the judge-round improvement:
- repetitive keyword stuffing should score below contextual responses on each task
- mixed-intent stuffing should be worse than a focused response
- apology-led boilerplate should not outrank a concrete task-aligned reply
- hard-task contextual behavior must stay at or above the current strong baseline

```python
def test_repetitive_reply_is_penalized_against_contextual_reply():
    ...
    assert repetitive.reward < contextual.reward
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_environment_contract.py tests/test_inference_policy.py`
Expected: at least one shortcut-shape assertion fails on the current baseline or exposes the missing guardrail.

- [ ] **Step 3: Write minimal implementation**

Do not implement yet. This step stays pending until Task 2.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_environment_contract.py tests/test_inference_policy.py`
Expected: PASS after the environment penalties are added.

- [ ] **Step 5: Commit**

```bash
git add tests/test_environment_contract.py tests/test_inference_policy.py
git commit -m "test: pin anti-shortcut reward behavior"
```

### Task 2: Tighten the environment reward model

**Files:**
- Modify: `envs/support_queue_env/server/your_environment.py:1-220`

- [ ] **Step 1: Inspect the reward flow**

Confirm the existing reward components, especially:
- route correctness
- keyword credit
- relevance credit
- generic and repetition penalties
- stuffing density and overlong penalties

Use the current `step()` implementation as the only place to change reward logic.

- [ ] **Step 2: Implement the minimal reward hardening**

Add or refine the following penalties in a conservative way:
- keyword spam penalty for repeated success-keyword usage with low relevance
- mixed-intent stuffing penalty for responses that combine stuffing vocabulary with high repetition
- apology-template penalty for short apology-led boilerplate with weak relevance
- keep contextual success responses near the current strong score band

Preserve:
- `clamp_open_score()` usage
- strict `(0, 1)` reward bounds
- deterministic outputs
- existing task routing semantics

- [ ] **Step 3: Run the focused contract and policy tests**

Run: `python -m pytest -q tests/test_environment_contract.py tests/test_inference_policy.py`
Expected: PASS, with shortcut examples scoring below contextual examples and strong contextual replies remaining high.

- [ ] **Step 4: Commit**

```bash
git add envs/support_queue_env/server/your_environment.py
git commit -m "feat: harden anti-shortcut reward penalties"
```

### Task 3: Validate judge-facing behavior end to end

**Files:**
- Modify: `scripts/judging_audit.py` only if a test exposes a missing audit case
- Modify: `tests/test_judging_audit.py` only if audit coverage needs to be pinned
- No changes expected to `inference.py`

- [ ] **Step 1: Run the full local gate**

Run:
```powershell
python -m pytest -q
python scripts/judging_audit.py
python scripts/probe_endpoints.py --base-url http://127.0.0.1:7861
```
Expected:
- pytest passes completely
- judging audit passes all checks
- endpoint probe stays at 17/17 pass

- [ ] **Step 2: Confirm no judge-contract regression**

Verify:
- `inference.py` still emits exactly START/STEP/END lines
- scores remain strictly between 0 and 1
- the hard task contextual score remains at least the current validated level
- shortcut scores are lower than contextual scores on the judge audit

- [ ] **Step 3: Save evidence for the candidate SHA**

Run: `python scripts/submission_pipeline.py pre-submit --save-artifacts-dir submission-artifacts`
Expected: GO, with a fresh timestamped evidence artifact for the worktree commit.

- [ ] **Step 4: Commit**

```bash
git add scripts/judging_audit.py tests/test_judging_audit.py envs/support_queue_env/server/your_environment.py
git commit -m "chore: validate judging hardening candidate"
```

### Task 4: Decide whether to merge to the frozen baseline

**Files:**
- None unless validation reveals an unexpected regression

- [ ] **Step 1: Compare metrics against the frozen baseline**

Record:
- contextual average score
- keyword stuffing average score
- repetitive keyword average score
- hard-task contextual score

- [ ] **Step 2: Merge only if the candidate is strictly better**

Merge criteria:
- contextual score stays unchanged or improves
- repetitive keyword stuffing drops
- mixed-intent and apology-template shortcuts do not outrank contextual replies
- full validation remains green

- [ ] **Step 3: Keep main frozen if results are unclear**

If the gain is not clearly measurable, stop at the worktree branch and do not merge back to `main`.
