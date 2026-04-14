# Deferred Items

## 2026-04-14

- Out of scope during `02-01`: the repository-wide pre-commit pytest run failed in `tests/test_postgres_backtest.py` because PostgreSQL backtest schema and `postgres_backtest` implementation work is not present in this workspace slice. Affected failures:
  - `test_bootstrap_schema_applies_all_checked_in_sql_files`
  - `test_save_backtest_writes_run_window_and_step_rows`
  - `test_backtest_step_stats_view_exposes_grouped_stats_for_one_run`
