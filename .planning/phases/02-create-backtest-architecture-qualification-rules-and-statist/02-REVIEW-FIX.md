---
phase: 02
fixed_at: 2026-04-14T15:35:42.8573125Z
review_path: .planning/phases/02-create-backtest-architecture-qualification-rules-and-statist/02-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-04-14T15:35:42.8573125Z
**Source review:** `.planning/phases/02-create-backtest-architecture-qualification-rules-and-statist/02-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-01: Stored run coverage records the requested day instead of the actual candle span

**Status:** fixed
**Files modified:** `src/crypto_minute_backtest.py`, `tests/test_crypto_minute_backtest.py`, `AgentHelper/ProjectFiles/DescriptionFiles/src/crypto_minute_backtest.py.md`
**Commit:** `1a7f071`
**Applied fix:** `main()` now persists the actual first and last loaded candle timestamps as run coverage while keeping the requested day range for printed summaries, and the regression test asserts the saved coverage comes from the loaded frame.

### WR-02: The schema allows step rows to point at a window from a different run

**Status:** fixed
**Files modified:** `db/init/002_phase2_backtest_schema.sql`, `tests/test_postgres_backtest.py`
**Commit:** `c43bdad`
**Applied fix:** Added a composite `(run_id, window_id)` uniqueness constraint on backtest windows and enforced it from prediction steps with a composite foreign key, plus an integration test that proves mismatched run/window inserts now fail.

### WR-03: The documented Windows wrapper path defaults to GPU-only Docker execution

**Status:** fixed
**Files modified:** `scripts/run_crypto_backtest.ps1`, `tests/test_script_wrappers.py`, `AgentHelper/ProjectFiles/DescriptionFiles/scripts/run_crypto_backtest.ps1.md`
**Commit:** `41989b6`
**Applied fix:** Changed the wrapper default backend to CPU, kept GPU opt-in, and added a contract test that verifies the no-flag path no longer injects `--gpus all`.

---

_Fixed: 2026-04-14T15:35:42.8573125Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
