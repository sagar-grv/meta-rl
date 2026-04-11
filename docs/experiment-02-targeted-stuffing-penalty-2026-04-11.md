# Experiment 02 - Targeted Stuffing Penalty

Date: 2026-04-11
Branch: exp/judging-improvements
Status: Candidate selected (improves anti-exploit score with no contextual regression)

## Change Tested

- Added a targeted exploit penalty for high stuffing-term overload.
- Kept existing penalties and reward bounds unchanged.

Updated file:
- envs/support_queue_env/server/your_environment.py

Penalty logic introduced:
- exploit_penalty = 0.12 when stuffing_count >= 6
- exploit_penalty = 0.05 when stuffing_count >= 4 and relevance_ratio < 0.30

## Verification Results

- Test suite: 55 passed
- Judging audit: 4 passed, 0 failed
- Contract and determinism checks: passed

## Metric Comparison (Baseline -> Experiment 02)

- avg(contextual): 0.890 -> 0.890 (no regression)
- avg(keyword_stuff): 0.510 -> 0.430 (improved)
- avg(repetitive_keyword): 0.437 -> 0.437 (unchanged)
- avg(overlong_irrelevant): 0.243 -> 0.243 (unchanged)
- hard-task contextual: 0.890 -> 0.890 (no regression)

## Decision

- Keep as candidate on experiment branch.
- Promote to main only after full pre-submit evidence gate and controlled live comparison.
