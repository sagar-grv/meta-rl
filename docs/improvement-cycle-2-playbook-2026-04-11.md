# Improvement Cycle 2 Playbook

Date: 2026-04-11
Branch: exp/improvement-cycle-2
Base main SHA: 7d52c4a36437e7efeb9129db545de3f11c529807

## Required Flow (Repeatable)

1. Keep main untouched.
2. Implement one small improvement on this branch.
3. Run validation gate:
   - python -m pytest -q
   - python scripts/judging_audit.py
   - python scripts/probe_endpoints.py --base-url https://sagar-grv-anything-you-want.hf.space
4. Deploy candidate to HF main only for validation testing.
5. Run strict evidence check pinned to candidate SHA.
6. If validated and improved, merge to main.
7. If not validated or not improved, do not merge; iterate again on this branch.

## Merge Criteria

- No contract regressions
- No score-range regressions
- Judging metrics equal or better on targeted objective
- Strict evidence gate returns GO on candidate SHA

## Rollback Rule

- If post-merge issues appear, immediately reset main to the pre-merge backup ref and push.

## Current Status

- Branch initialized from validated main.
- Ready for next isolated experiment.
