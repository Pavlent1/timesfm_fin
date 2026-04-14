---
status: partial
phase: 02-create-backtest-architecture-qualification-rules-and-statist
source: [02-VERIFICATION.md]
started: 2026-04-14T17:44:59.3960557+02:00
updated: 2026-04-14T20:52:00.0000000+02:00
---

## Current Test

[testing paused - 1 items outstanding]

## Tests

### 1. Docker Wrapper To Local PostgreSQL
expected: The container reaches PostgreSQL through `host.docker.internal`, writes rows into `market_data.backtest_runs`, `market_data.backtest_windows`, and `market_data.backtest_prediction_steps`, and does not create a SQLite backtest store.
result: issue
reported: "Running scripts/run_crypto_backtest.ps1 with the existing timesfm-fin image fails immediately inside the container with ModuleNotFoundError: No module named 'psycopg', so the PostgreSQL-backed runtime never starts."
severity: blocker

### 2. Per-Step Stats Operator Readability
expected: Querying `market_data.backtest_step_stats_vw` for a real run makes horizon-distance behavior easy to inspect, including step index, average normalized deviation, standard deviation, and overshoot/undershoot counts.
result: blocked
blocked_by: release-build
reason: "No stored backtest run exists in market_data.backtest_runs because the supported Docker wrapper path fails before execution. A host-side fallback could not create a run either because the local Python environment lacks the TimesFM runtime dependencies (jax/torch)."

## Summary

total: 2
passed: 0
issues: 1
pending: 0
skipped: 0
blocked: 1

## Gaps

- truth: "The Docker wrapper starts the PostgreSQL-backed backtest runtime inside the container and persists a real run without falling back to SQLite."
  status: failed
  reason: "Observed during repo-executed UAT: scripts/run_crypto_backtest.ps1 launched the container, but src/crypto_minute_backtest.py crashed immediately with ModuleNotFoundError: No module named 'psycopg'."
  severity: blocker
  test: 1
  root_cause: "Dockerfile does not install psycopg or the PostgreSQL-backed runtime dependencies now required by src/crypto_minute_backtest.py, so the image used by scripts/run_crypto_backtest.ps1 is not aligned with the Phase 2 code path."
  artifacts:
    - path: "Dockerfile"
      issue: "Image install step only provisions the inference stack and omits psycopg required by the PostgreSQL runtime."
    - path: "scripts/run_crypto_backtest.ps1"
      issue: "Wrapper correctly launches the image, but the image contents are stale relative to the runtime's dependency needs."
  missing:
    - "Add psycopg and the required runtime dependency set for src/crypto_minute_backtest.py to the Docker image build."
    - "Rebuild the timesfm-fin image and rerun the wrapper against PostgreSQL."
  debug_session: ""
