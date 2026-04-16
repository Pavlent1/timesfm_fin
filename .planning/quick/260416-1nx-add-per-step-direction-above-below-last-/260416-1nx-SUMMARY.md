# Quick Task 260416-1nx Summary

**Task:** add per-step direction-above-below-last-input accuracy metric to backtests
**Date:** 2026-04-15
**Status:** Completed

## What changed

- added `direction_guess_correct` to `src/backtest_metrics.py` so each step records whether predicted and actual closes end on the same side of the last input close
- added `direction_guess_accuracy_pct` to both backtest summary paths:
  - direct Python aggregation in `src/crypto_prediction_backtest.py`
  - PostgreSQL view aggregation in `db/init/002_phase2_backtest_schema.sql` and `src/postgres_backtest.py`
- included the raw `direction_guess_correct` flag in strategy detail CSV rows
- refreshed the affected tests and approved-scope file descriptions

## Validation

- passed: `.venv\Scripts\python.exe -m pytest tests/test_backtest_metrics.py tests/test_crypto_prediction_backtest.py tests/test_crypto_minute_backtest.py tests/test_postgres_backtest.py`
