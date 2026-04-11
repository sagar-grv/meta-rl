# Cycle 5 Experiment 01 - Shortcut Suppression Bundle

Date: 2026-04-11
Branch: exp/improvement-cycle-5
Status: Candidate selected

## Features Added

Three additional anti-shortcut features were added on top of Cycle 4:

1. High repetition penalty
- Penalizes highly repetitive replies when token volume is sufficient.

2. Template route penalty
- Penalizes low-relevance replies even when route is correct, reducing template-style score inflation.

3. Short keyword-only penalty
- Penalizes very short keyword-triggered replies with poor context relevance.

File:
- envs/support_queue_env/server/your_environment.py

## Validation

- pytest: 55 passed
- judging_audit: 4/4 passed
- endpoint_probe: 17/17 passed
- openenv validate: passed

## Metric Delta (Cycle 5 Baseline -> Experiment)

- avg(contextual): 0.890 -> 0.890 (unchanged)
- avg(keyword_stuff): 0.337 -> 0.337 (unchanged)
- avg(polite_generic): 0.457 -> 0.423 (improved)
- avg(one_template): 0.517 -> 0.500 (improved)
- avg(repetitive_keyword): 0.437 -> 0.420 (improved)
- avg(keyword_only): 0.210 -> 0.193 (improved)
- avg(overlong_irrelevant): 0.130 -> 0.110 (improved)
- hard-task contextual: 0.890 -> 0.890 (unchanged)

## Decision

Keep as Cycle 5 candidate. The bundle improves several shortcut profiles while preserving core task and contract behavior.
