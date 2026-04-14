---
phase: 02-create-backtest-architecture-qualification-rules-and-statist
reviewed: 2026-04-14T15:27:31Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - src/backtest_metrics.py
  - tests/test_backtest_metrics.py
  - db/init/002_phase2_backtest_schema.sql
  - src/postgres_backtest.py
  - src/bootstrap_postgres.py
  - src/postgres_dataset.py
  - tests/test_postgres_backtest.py
  - src/crypto_minute_backtest.py
  - scripts/run_crypto_backtest.ps1
  - README.md
  - db/README.md
  - tests/test_crypto_minute_backtest.py
  - tests/test_script_wrappers.py
  - tests/test_docs_contract.py
  - tests/test_schema_bootstrap.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-14T15:27:31Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed the Phase 02 backtest metric, PostgreSQL persistence, runtime migration, wrapper, and doc changes at standard depth. The scoped pytest suites passed (`tests/test_backtest_metrics.py`, `tests/test_crypto_minute_backtest.py`, `tests/test_postgres_backtest.py`, `tests/test_schema_bootstrap.py`, `tests/test_script_wrappers.py`, `tests/test_docs_contract.py`), but three warning-level issues remain: one reproducibility bug in stored run coverage metadata, one schema-level integrity hole in the canonical backtest store, and one wrapper default that breaks the documented Windows path on CPU-only Docker hosts.

## Warnings

### WR-01: Stored run coverage records the requested day instead of the actual candle span

**File:** `src/crypto_minute_backtest.py:730-753`
**Issue:** `main()` computes `start_dt, end_dt = day_bounds_utc(args.day)` and passes those values straight into `save_backtest()`. `save_backtest()` persists them into `market_data.backtest_runs.data_start_utc/data_end_utc`, so partial-day datasets or gaps are recorded as full-day coverage even when the loaded frame only spans part of that day. I reproduced this with a frame covering `2024-04-01T12:00:00Z` through `2024-04-01T12:06:00Z`; the stored run still claimed `2024-04-01T00:00:00Z` through `2024-04-02T00:00:00Z`. That makes BT-04-style reproduction and source-coverage auditing unreliable.
**Fix:**
```python
coverage_start = pd.Timestamp(frame["open_time_utc"].iloc[0]).to_pydatetime()
coverage_end = pd.Timestamp(frame["open_time_utc"].iloc[-1]).to_pydatetime()

run_id = save_backtest(
    conn=conn,
    args=args,
    start_dt=coverage_start,
    end_dt=coverage_end,
    metrics=metrics,
    window_rows=window_rows,
)
```
If the intent is to store both requested and actual coverage, add separate columns instead of overloading `data_start_utc` and `data_end_utc`.

### WR-02: The schema allows step rows to point at a window from a different run

**File:** `db/init/002_phase2_backtest_schema.sql:31-43`
**Issue:** `market_data.backtest_prediction_steps` stores both `run_id` and `window_id`, but it only enforces independent foreign keys. PostgreSQL therefore accepts rows where `run_id` belongs to one backtest run and `window_id` belongs to another. I verified that an insert with `run_id=2` and a `window_id` owned by run `1` succeeds. Because `market_data.backtest_step_stats_vw` groups on the stored `run_id`, a mismatched row silently corrupts per-run statistics.
**Fix:**
```sql
ALTER TABLE market_data.backtest_windows
    ADD CONSTRAINT backtest_windows_run_window_unique
    UNIQUE (run_id, window_id);

ALTER TABLE market_data.backtest_prediction_steps
    ADD CONSTRAINT backtest_steps_run_window_fk
    FOREIGN KEY (run_id, window_id)
    REFERENCES market_data.backtest_windows (run_id, window_id)
    ON DELETE CASCADE;
```
An even cleaner alternative is to drop `run_id` from `backtest_prediction_steps` entirely and derive it through `backtest_windows` in the stats view.

### WR-03: The documented Windows wrapper path defaults to GPU-only Docker execution

**File:** `scripts/run_crypto_backtest.ps1:1-19`
**Issue:** The wrapper defaults `$Backend` to `"gpu"`, and the README examples use `.\scripts\run_crypto_backtest.ps1 -Day 2026-04-11` without overriding that default. I confirmed the generated Docker command includes `--gpus all` when no backend is specified. On Windows hosts using Docker as the recommended orchestration path but without NVIDIA container support, the documented command fails immediately instead of running the backtest.
**Fix:**
```powershell
[string]$Backend = "cpu"
```
If GPU should stay available, make it opt-in and update the README examples to show `-Backend gpu` explicitly rather than relying on a GPU-only default.

---

_Reviewed: 2026-04-14T15:27:31Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
