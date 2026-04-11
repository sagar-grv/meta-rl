# Cycle 6 Experiment 01 - Large Anti-Shortcut Bundle

Date: 2026-04-12
Branch: exp/improvement-cycle-6
Status: Candidate selected

## Features Added

A larger feature set was introduced in one experiment pass:

1. Keyword spam penalty
- Penalizes repeated success-keyword usage with weak relevance.

2. Mixed-intent stuffing penalty
- Penalizes responses that combine high stuffing with high repetition.

3. Apology-template penalty
- Penalizes short apology-led low-relevance responses.

Note:
- A temporary context-coverage bonus was tested and then removed after it raised keyword-stuff score. Final candidate excludes that bonus.

File:
- envs/support_queue_env/server/your_environment.py

## Validation

- pytest: 55 passed
- judging_audit: 4/4 passed
- endpoint_probe: 17/17 passed
- openenv validate: passed

## Metric Delta (Cycle 6 Baseline -> Experiment)

- avg(contextual): 0.890 -> 0.890 (unchanged)
- avg(keyword_stuff): 0.337 -> 0.337 (non-regression)
- avg(polite_generic): 0.423 -> 0.423 (unchanged)
- avg(one_template): 0.500 -> 0.500 (unchanged)
- avg(repetitive_keyword): 0.420 -> 0.397 (improved)
- avg(keyword_only): 0.193 -> 0.193 (unchanged)
- avg(overlong_irrelevant): 0.110 -> 0.110 (unchanged)
- hard-task contextual: 0.890 -> 0.890 (unchanged)

## Decision

Keep as cycle-6 candidate. It delivers a targeted improvement on repetitive-keyword shortcuts with no judged-metric regressions.
