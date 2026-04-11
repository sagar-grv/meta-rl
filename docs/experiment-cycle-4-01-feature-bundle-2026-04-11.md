# Cycle 4 Experiment 01 - Multi-Feature Anti-Exploit Bundle

Date: 2026-04-11
Branch: exp/improvement-cycle-4
Status: Candidate selected

## Features Added

Three new anti-exploit features were added together:

1. Off-topic verbosity penalty
- Penalty when reply is long and extremely low relevance.

2. Keyword-route mismatch penalty
- Penalty when the success keyword is present but route selection is wrong.

3. Stuffing-density penalty
- Penalty when stuffing terms make up a high share of the reply.

File:
- envs/support_queue_env/server/your_environment.py

## Validation

- pytest: 55 passed
- judging_audit: 4/4 passed
- endpoint_probe: 17/17 passed
- openenv validate: passed

## Metric Delta (Cycle 4 Baseline -> Experiment)

- avg(contextual): 0.890 -> 0.890 (unchanged)
- avg(keyword_stuff): 0.390 -> 0.337 (improved)
- avg(one_template): 0.540 -> 0.517 (improved)
- avg(overlong_irrelevant): 0.177 -> 0.130 (improved)
- hard-task contextual: 0.890 -> 0.890 (unchanged)

## Decision

Keep as Cycle 4 candidate. This bundle improves multiple shortcut profiles while preserving core task performance.
