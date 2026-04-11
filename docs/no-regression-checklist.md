# No-Regression Checklist

Use this checklist before any future submission update.

## 1) Local correctness

- Run tests: python -m pytest -q
- Run local judging audit: python scripts/judging_audit.py
- Run inference smoke once and verify each task emits a single START/STEP/END sequence.

## 2) Log contract safety

- Ensure END line contains explicit score field and rewards field.
- Ensure all task scores printed in logs are strictly between 0 and 1.
- Avoid ambiguous tokens that can be parsed as boundary scores.
- Keep logs single-line and deterministic.

## 3) Endpoint contract safety

- Run endpoint probe against local or deployed URL:
  python scripts/probe_endpoints.py --base-url <url>
- Confirm reset, step, state, invalid payload rejection, deterministic checks all pass.

## 4) Deployment control

- Push code to GitHub and Hugging Face Space remotes.
- Verify runtime stage is RUNNING on expected SHA.
- Do not submit while runtime is RUNNING_BUILDING on old SHA.

## 5) Frozen evidence gate

- Run strict evidence command with expected SHA.
- Require GO before every submission.
- Save timestamped artifacts for each submission cycle.

## 6) Submission discipline

- Submit exactly once per frozen SHA check.
- Avoid pushing new commits during an active validation run.
- If a failure occurs, classify failure type first, patch minimally, and re-run the full gate.
