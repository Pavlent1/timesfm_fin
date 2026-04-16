---
status: partial
phase: 03-train-the-model-on-1-minute-crypto-candles
source: [03-VERIFICATION.md]
started: 2026-04-16T15:59:00Z
updated: 2026-04-16T15:59:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Real Manual Training Run
expected: A real `src/train_from_postgres.py` run in the supported TimesFM v1 environment creates checkpoint artifacts plus `run_manifest.json`, `environment_snapshot.json`, `evaluation_summary.json`, and `backtest_summary.json`, and records the explicit parent checkpoint.
result: pending

### 2. Real Comparison Report Readability
expected: Running `src/compare_training_runs.py` against two real run bundles produces `comparison_summary.json` and `comparison_summary.md` that clearly show parent checkpoint, prepared-bundle identity, holdout ranges, evaluation summaries, and referenced backtest ids.
result: pending

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
