# Improvement Cycle 3 Playbook

Date: 2026-04-11
Branch: exp/improvement-cycle-3
Base main SHA: 7d52c4a36437e7efeb9129db545de3f11c529807

## Priority Rule

Only attempt critical, high-confidence improvements.
No speculative refactors.
No broad behavior changes.

## Required Flow (Repeatable)

1. Keep main untouched.
2. Add exactly one small critical improvement.
3. Run validation gate:
   - python -m pytest -q
   - python scripts/judging_audit.py
   - python scripts/probe_endpoints.py --base-url https://sagar-grv-anything-you-want.hf.space
   - openenv validate
4. Deploy candidate SHA to HF main for live check.
5. Run strict evidence pinned to candidate SHA.
6. If validated and improved, merge to main.
7. If not validated or not improved, do not merge and iterate on this branch.

## Merge Criteria

- Zero contract regressions
- Zero score-range regressions
- Judging-relevant metric improvement or strict non-regression on target risk
- Strict evidence returns GO for candidate SHA

## Rollback Rule

If post-merge issue appears, reset main to the pre-merge backup ref and push immediately.

## Current Status

Cycle initialized from validated main and ready for one controlled experiment.
