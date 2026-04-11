# Baseline Capture - Experiment Branch

Date: 2026-04-11
Branch: exp/judging-improvements
Branch HEAD: fd72d6a29a782f3c27dca3761359f86aef59651d
Live Runtime SHA at capture: 431a1943d536296b4db989e2a973175346315e55

## Baseline Commands Run

1. python -m pytest -q
2. python scripts/judging_audit.py
3. python scripts/probe_endpoints.py --base-url https://sagar-grv-anything-you-want.hf.space
4. python scripts/submission_evidence.py --strict --space-id sagar-grv/anything_you_want --base-url https://sagar-grv-anything-you-want.hf.space --expected-sha 431a1943d536296b4db989e2a973175346315e55 --output submission-artifacts/baseline-capture-live-sha.md

## Results

- Test suite: 55 passed
- Judging audit: 4 passed, 0 failed
- Endpoint probe: 17 passed, 0 failed
- Strict evidence: GO

## Judging Audit Snapshot

- interface_contract: PASS
- policy_ordering: PASS
- hard_task_challenge: PASS
- determinism: PASS

## Notes

- A first strict evidence run against a different expected SHA correctly returned NO-GO due to SHA mismatch.
- Final strict evidence rerun pinned to the live runtime SHA returned GO and is the canonical baseline evidence packet for this branch.

## Evidence Artifacts

- submission-artifacts/baseline-capture-exp-branch.md
- submission-artifacts/baseline-capture-live-sha.md
- submission-artifacts/baseline-capture-live-sha.json
