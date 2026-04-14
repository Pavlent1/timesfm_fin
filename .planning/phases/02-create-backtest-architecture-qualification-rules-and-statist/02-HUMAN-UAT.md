---
status: partial
phase: 02-create-backtest-architecture-qualification-rules-and-statist
source: [02-VERIFICATION.md]
started: 2026-04-14T17:44:59.3960557+02:00
updated: 2026-04-14T17:44:59.3960557+02:00
---

## Current Test

awaiting human testing

## Tests

### 1. Docker Wrapper To Local PostgreSQL
expected: The container reaches PostgreSQL through `host.docker.internal`, writes rows into `market_data.backtest_runs`, `market_data.backtest_windows`, and `market_data.backtest_prediction_steps`, and does not create a SQLite backtest store.
result: pending

### 2. Per-Step Stats Operator Readability
expected: Querying `market_data.backtest_step_stats_vw` for a real run makes horizon-distance behavior easy to inspect, including step index, average normalized deviation, standard deviation, and overshoot/undershoot counts.
result: pending

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
