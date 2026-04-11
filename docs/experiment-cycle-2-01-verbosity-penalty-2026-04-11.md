# Cycle 2 Experiment 01 - Low-Relevance Verbosity Penalty

Date: 2026-04-11
Branch: exp/improvement-cycle-2
Status: Candidate selected

## Change

Added a targeted penalty for long, low-relevance replies:
- low_relevance_verbosity_penalty = 0.08 when token_count >= 12 and relevance_ratio < 0.12

File:
- envs/support_queue_env/server/your_environment.py

## Validation

- pytest: 55 passed
- judging_audit: 4/4 passed
- endpoint_probe: 17/17 passed
- openenv validate: passed

## Metric Delta (Cycle 2 Baseline -> Experiment)

- avg(contextual): 0.890 -> 0.890 (unchanged)
- avg(keyword_stuff): 0.430 -> 0.430 (unchanged)
- avg(repetitive_keyword): 0.437 -> 0.437 (unchanged)
- avg(overlong_irrelevant): 0.243 -> 0.190 (improved)
- hard-task contextual: 0.890 -> 0.890 (unchanged)

## Decision

Keep as cycle-2 candidate. Safe for controlled deployment test before merge decision.
