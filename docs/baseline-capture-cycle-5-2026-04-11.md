# Baseline Capture - Cycle 5

Date: 2026-04-11
Branch: exp/improvement-cycle-5
Base SHA: 73d8f3d104da8bd7eaca4e84c7392d7da70c2b8d

## Commands Run

1. python -m pytest -q
2. python scripts/judging_audit.py

## Results

- Test suite: 55 passed
- Judging audit: 4 passed, 0 failed

## Metric Snapshot

- avg(contextual)=0.890
- avg(keyword_stuff)=0.337
- avg(one_template)=0.517
- avg(repetitive_keyword)=0.437
- avg(keyword_only)=0.210
- avg(overlong_irrelevant)=0.130
- hard-task contextual=0.890

## Decision

Cycle 5 baseline is healthy and ready for a new multi-feature shortcut-suppression bundle.
