# Cycle 3 Experiment 02 - Stuffing Penalty Tightening

Date: 2026-04-11
Branch: exp/improvement-cycle-3
Status: Candidate selected

## Change

Strengthened the existing anti-stuffing penalties while keeping the verbosity tightening in place:
- stuffing_penalty = 0.32 when stuffing_count >= 4
- exploit_penalty = 0.14 when stuffing_count >= 6
- exploit_penalty = 0.06 when stuffing_count >= 4 and relevance_ratio < 0.30

File:
- envs/support_queue_env/server/your_environment.py

## Validation

- pytest: 55 passed
- judging_audit: 4/4 passed
- endpoint_probe: 17/17 passed
- openenv validate: passed

## Metric Delta (Cycle 3 Previous Candidate -> Experiment)

- avg(contextual): 0.890 -> 0.890 (unchanged)
- avg(keyword_stuff): 0.430 -> 0.390 (improved)
- avg(repetitive_keyword): 0.437 -> 0.437 (unchanged)
- avg(overlong_irrelevant): 0.190 -> 0.177 (unchanged)
- hard-task contextual: 0.890 -> 0.890 (unchanged)

## Decision

Keep as the next cycle-3 candidate. It improves the stuffing shortcut without regressing the main task score.
