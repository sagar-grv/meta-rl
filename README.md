---
title: Support Queue OpenEnv
emoji: 📨
colorFrom: gray
colorTo: yellow
sdk: docker
pinned: false
---

# Support Queue OpenEnv

Support Queue OpenEnv is a deterministic customer support benchmark built for the OpenEnv Round 1 submission flow. It simulates common real-world support work such as triaging login issues, drafting refund-safe replies, and escalating disputes with compliant handoffs.

The environment is designed to be simple to run, easy to validate, and useful for evaluating agent behavior on a realistic business workflow.

## Tasks

The benchmark includes three graded tasks with increasing difficulty:

- `ticket_triage` - route a login-related ticket to support and respond with a useful diagnostic question.
- `reply_drafting` - draft a policy-safe reply for a refund request.
- `escalation_resolution` - escalate a billing dispute with a compliant handoff.

Each task returns a score in the range `0.0` to `1.0`.

## Environment Interface

The environment follows the OpenEnv `reset() / step() / state()` contract.

### Action Space

`SupportQueueAction`

- `route`: routing decision for the ticket.
- `reply`: the response text written by the agent.

### Observation Space

`SupportQueueObservation`

- `ticket_id`: identifier for the active ticket.
- `status`: current ticket status.
- `subject`: short ticket subject line.
- `summary`: fuller ticket description.

### Reward Signal

The reward function is deterministic and uses task-specific signals:

- exact route match
- required keyword match
- task-specific compliance phrasing
- optional penalty for vague or generic replies

## Repository Structure

- `envs/support_queue_env/` - environment implementation, models, and task registry
- `envs/support_queue_env/server/` - FastAPI app and environment wrapper
- `inference.py` - baseline script used for evaluation
- `tests/` - automated contract and inference tests
- `Dockerfile` - Hugging Face Space container definition

## Setup

Requirements:

- Python 3.10+
- Docker
- Hugging Face account/token for deployment

Install and test locally:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest -q
```

## Baseline Inference

The root-level `inference.py` uses the OpenAI client and reads runtime configuration from environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Example:

```powershell
$env:API_BASE_URL="https://router.huggingface.co/v1"
$env:MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
$env:HF_TOKEN="hf_your_token"
$env:PYTHONPATH="envs;."
python .\inference.py
```

The script emits structured logs in the required `[START]`, `[STEP]`, and `[END]` format.

## Container

The Docker image listens on port `7860`, which is compatible with Hugging Face Spaces.

## Validation

Before submission, run the local checks and the submission validator against your live Space URL.

```powershell
pytest -q
python .\inference.py
bash ./scripts/validate-submission.sh https://your-space-name.hf.space .
```

## Local Submission Pipeline

Use the local pipeline to check the repo before every submission and to turn dashboard output into the next improvement pass.

Preflight checks against a local server:

```powershell
$env:PYTHONPATH="envs;."
python .\scripts\submission_pipeline.py preflight --base-url http://127.0.0.1:7861
```

Analyze pasted dashboard output or a saved text file:

```powershell
python .\scripts\submission_pipeline.py analyze-dashboard --input-text "Phase 2 failed: each task's score must be strictly between 0 and 1."
python .\scripts\submission_pipeline.py analyze-dashboard --input-file .\dashboard-output.txt
```

The analyzer maps dashboard text to one of these buckets: score-range, reproducibility, endpoint-contract, logging-format, deployment-runtime, anti-exploit, or quality-regression. It also returns a recommended fix and a next regression case to add before the next submission.

### Judging-Focused Local Audit

Run this before a final resubmission to evaluate six judging-oriented layers locally (interface contract, anti-exploit ordering, hard-task challenge behavior, and determinism checks).

```powershell
$env:PYTHONPATH="envs;."
python .\scripts\judging_audit.py
```

This command exits with a non-zero code if any audit gate fails.

### Submission Evidence Pack

Capture a frozen submission snapshot from the live Hugging Face Space before resubmitting. This records the repo SHA, Space runtime SHA/stage, live endpoint probe results, and optional run/build log snippets.

```powershell
$env:PYTHONPATH="envs;."
$env:HF_SPACE_ID="sagar-grv/anything_you_want"
$env:SPACE_BASE_URL="https://sagar-grv-anything-you-want.hf.space"
$env:EXPECTED_SPACE_SHA="<commit-sha-to-freeze>"
$env:HF_TOKEN="<hf-token-with-space-read-access>"
python .\scripts\submission_evidence.py --strict --output .\submission-evidence.md
```

The command writes both `submission-evidence.md` and `submission-evidence.json`. Use `--strict` to make the command fail when the live Space is not on the expected SHA or when any probe check fails.

### Evaluator-like Local Endpoint Probe

To catch edge-case API issues before submission, run a local probe that mimics common evaluator checks (reset without body, task-by-task step scoring, strict score bounds, state transitions, invalid payload rejection, and deterministic output checks).

```powershell
$env:PYTHONPATH="envs;."
python -m uvicorn support_queue_env.server.app:app --host 127.0.0.1 --port 7861
python .\scripts\probe_endpoints.py --base-url http://127.0.0.1:7861
```

The probe exits non-zero if any check fails, so you can use it in CI or pre-submit scripts.

---
title: Anything You Want
emoji: 👀
colorFrom: gray
colorTo: yellow
sdk: docker
pinned: false
---

# Support Queue OpenEnv Submission

This repository contains a customer support queue environment built for the OpenEnv Round 1 requirements.

## Environment

The environment simulates a support desk where an agent must triage, draft a policy-safe reply, or escalate a ticket depending on the selected task tier.

## Tasks

- `ticket_triage` - easy
- `reply_drafting` - medium
- `escalation_resolution` - hard

## Action Space

`SupportQueueAction` uses two fields:

- `route`: the agent's routing decision.
- `reply`: the text response generated by the agent.

## Observation Space

`SupportQueueObservation` includes:

- `ticket_id`
- `status`
- `subject`
- `summary`

## Setup

Install the project in a Python 3.10+ environment and run the tests with pytest.

## Baseline

The root-level `inference.py` uses the OpenAI client with `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` to evaluate all three tasks and emit `[START]`, `[STEP]`, and `[END]` logs.

