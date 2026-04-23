# Quick Task 260418-qj7: implement per-step conditional backtest metrics for thresholded direction analysis

**Completed:** 2026-04-23
**Code Commit:** `71a07f6`

## Delivered

- added `absolute_move_pct_from_input()` plus the locked step-1-through-step-5 conditional threshold table in `src/backtest_metrics.py`
- added Python-side conditional cohort aggregation for `actual_move_pct` and `predicted_move_pct` in `src/crypto_minute_backtest.py`
- appended a second backtest report table titled `Conditional direction accuracy by move threshold` with the required cohort and lift columns
- extended focused pytest coverage for the new helpers, cohort math, and report rendering

## Verification

- targeted validation: `.venv\Scripts\python.exe -m pytest tests/test_backtest_metrics.py tests/test_crypto_minute_backtest.py`
- full repo validation via the pre-commit hook during commit: `107 passed`
