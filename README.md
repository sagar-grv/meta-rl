---
title: Support Queue OpenEnv
emoji: "📨"
colorFrom: gray
colorTo: yellow
sdk: docker
pinned: false
---

# Support Queue OpenEnv

Support Queue OpenEnv is a deterministic customer-support benchmark for OpenEnv Round 1 style evaluation. It simulates three common support tasks and exposes standard `reset`, `step`, and `state` APIs.

## Validation Snapshot

- Round 1 deep validation: passed (submission #74)
- Freeze tag: `round1-submission74-validated`
- Runtime contract: score remains strictly within `(0, 1)` and deterministic checks are enforced

## Tasks

- `ticket_triage`: route a login-related ticket and provide a useful diagnostic response
- `reply_drafting`: draft a policy-safe response for a refund request
- `escalation_resolution`: escalate a billing dispute with a compliant handoff

## Repository Structure

- `envs/support_queue_env/`: environment logic, models, and task registry
- `envs/support_queue_env/server/`: FastAPI server and environment wrapper
- `web/index.html`: browser testing dashboard
- `inference.py`: baseline inference entrypoint (required at repo root)
- `tests/`: contract, endpoint, and inference tests
- `scripts/`: preflight, evidence, and probing utilities
- `submission-artifacts/`: generated evidence and audit snapshots
- `Dockerfile`: Hugging Face Space compatible runtime image

## Local Setup

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Run all tests:

```powershell
python -m pytest -q
```

## Testing Dashboard

The dashboard is served at `/ui/` and provides manual testing for:

- `POST /ui-api/reset`
- `POST /ui-api/step`
- `GET /ui-api/state`

Start locally:

```powershell
$env:PYTHONPATH="envs;."
python -m uvicorn support_queue_env.server.app:app --host 127.0.0.1 --port 7860
```

Open: `http://127.0.0.1:7860/ui/`

### How To Use

1. Select a `Task` and `Seed`
2. Click `Load Example` (optional) to prefill a tested scenario
3. Click `Reset` to initialize task state
4. Click `Step` to evaluate a route/reply pair
5. Use `State` to inspect step count and current environment state
6. Review reward and JSON response in the right-side log panel

### Built-in Example Scenarios

- `Ticket triage - strong`
  - route: `support`
  - expected behavior: high score with login/recovery-focused wording
- `Reply drafting - policy safe`
  - route: `support`
  - expected behavior: good score with refund-policy-safe language
- `Escalation resolution - compliant handoff`
  - route: `escalate`
  - expected behavior: high score with explicit escalation + handoff context
- `Anti-shortcut check - repetitive spam`
  - route: `support`
  - expected behavior: lower score due to repetitive keyword stuffing

Use `Run Example (Reset + Step)` for one-click execution of the selected scenario.

## Baseline Inference

The root `inference.py` uses OpenAI-compatible API settings:

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

Log output contract:

```text
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> score=<0.00-0.99> steps=<n> rewards=<r1,r2,...,rn>
```

## Submission Safety Checks

Local preflight:

```powershell
$env:PYTHONPATH="envs;."
python .\scripts\submission_pipeline.py preflight --base-url http://127.0.0.1:7860
```

Strict live evidence pack:

```powershell
$env:PYTHONPATH="envs;."
$env:HF_SPACE_ID="sagar-grv/anything_you_want"
$env:SPACE_BASE_URL="https://sagar-grv-anything-you-want.hf.space"
$env:EXPECTED_SPACE_SHA="<commit-sha>"
$env:HF_TOKEN="<hf-token>"
python .\scripts\submission_evidence.py --strict --output .\submission-evidence.md
```

## Container

The Docker image serves on port `7860` and is compatible with Hugging Face Spaces.
