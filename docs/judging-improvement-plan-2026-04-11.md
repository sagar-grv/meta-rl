# Judging Improvement Branch Plan

Date: 2026-04-11
Working branch: exp/judging-improvements
Stable baseline branch: main
Stable validated SHA: 8619a3ad1a74832a9dacea23270d907e0ea1f03e

## Objective

Improve judging performance without risking the validated baseline.

## Rules

1. Never edit main directly.
2. Make one small change per experiment.
3. Run full validation gate after every change.
4. Merge only if all gates pass and the change is clearly better.
5. If any gate fails, discard the experiment branch.

## Experiment Sequence

1. Baseline capture on this branch.
2. Anti-exploit reward tuning pass.
3. Hidden-case robustness pass.
4. Determinism and edge-case pass.
5. End to end strict pre-submit evidence pass.

## Validation Gate

1. Test suite must pass completely.
2. Endpoint probe must pass all checks.
3. Inference output must remain parser safe and in strict score range.
4. Live space runtime SHA must match expected SHA.
5. Strict evidence command must return GO.

## Merge Criteria

1. No contract regressions.
2. No score-range regressions.
3. Clear measurable improvement in judging-relevant checks.
4. At least one fresh GO evidence artifact for the candidate SHA.

## Rollback Policy

1. If improvement is uncertain, do not merge.
2. Keep main at validated baseline.
3. If needed, delete experiment branch and recreate from main.
