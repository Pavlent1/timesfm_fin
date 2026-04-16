---
phase: 03-train-the-model-on-1-minute-crypto-candles
plan: "05"
subsystem: reporting
tags: [lineage, reporting, comparison, docs]
requires:
  - phase: 03-train-the-model-on-1-minute-crypto-candles
    provides: deterministic Phase 3 run bundles with explicit holdout summaries
provides:
  - per-run lineage manifests
  - cross-run comparison summaries in JSON and Markdown
  - updated operator docs for the manual Phase 3 reporting flow
affects: [phase-03-reporting, reproducibility, docs]
tech-stack:
  added: []
  patterns: [file-first lineage normalization, comparison-ready run bundles]
key-files:
  created:
    - src/training_lineage.py
    - src/compare_training_runs.py
    - tests/test_training_lineage.py
    - AgentHelper/ProjectFiles/DescriptionFiles/src/training_lineage.py.md
    - AgentHelper/ProjectFiles/DescriptionFiles/src/compare_training_runs.py.md
  modified:
    - README.md
key-decisions:
  - "Phase 3 run reporting is anchored on run_manifest.json plus real evaluation/backtest artifacts, not on anonymous checkpoint directories."
  - "Comparison output is both machine-readable and operator-readable so later manual runs can be inspected without requerying raw metadata by hand."
patterns-established:
  - "Comparison reporting rejects incomplete or metadata-only run bundles before emitting output."
  - "Lineage manifests normalize per-symbol train/holdout ranges, copied config identity, and supplemental backtest provenance into one per-run artifact."
requirements-completed: [MODEL-01]
duration: 31 min
completed: 2026-04-16
---

# Phase 03 Plan 05: Lineage And Comparison Summary

**Per-run lineage manifests plus machine-readable and operator-readable run comparison reports**

## Performance

- **Duration:** 31 min
- **Started:** 2026-04-16T15:21:00Z
- **Completed:** 2026-04-16T15:52:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `tests/test_training_lineage.py` to lock the D-17/D-18 reporting contract before implementation, including rejection of incomplete run bundles and explicit comparison of dataset, holdout, parent-checkpoint, and backtest provenance differences.
- Added `src/training_lineage.py` so each completed Phase 3 run can be normalized into a `lineage_manifest.json` with explicit checkpoint parentage, selected symbols, per-symbol train/holdout ranges, copied config identity, and real evaluation/backtest summaries.
- Added `src/compare_training_runs.py` so operators can compare two or more run bundles and emit both `comparison_summary.json` and `comparison_summary.md`, with optional PostgreSQL backtest metadata resolution.
- Updated `README.md` to document the manual Phase 3 bundle -> train -> compare flow end to end.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the lineage and comparison contract tests** - `8b6fa9b` (test)
2. **Task 2: Implement per-run lineage and summary artifact generation** - `d16dfc5` (feat)
3. **Task 3: Implement the run-comparison CLI and operator docs** - `10b1e1d` (feat)

**Plan metadata:** completed

## Files Created/Modified

- `tests/test_training_lineage.py` - Locks the per-run lineage and cross-run comparison contract.
- `src/training_lineage.py` - Writes `lineage_manifest.json` from completed run bundles and rejects incomplete bundles.
- `src/compare_training_runs.py` - Emits JSON and Markdown comparison outputs for two or more run bundles.
- `README.md` - Documents the manual Phase 3 reporting step.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/training_lineage.py.md` - Mirrors the lineage-helper responsibility.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/compare_training_runs.py.md` - Mirrors the comparison/reporting responsibility.

## Decisions Made

- Bound the reporting layer to the explicit run bundle contract from `03-04` instead of creating a second reporting-only metadata store.
- Kept comparison output file-first and CLI-first, with PostgreSQL lookups remaining optional enrichment for referenced `backtest_run_id` values.
- Emitted both JSON and Markdown so downstream automation and human review can consume the same comparison result without translating formats manually.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Real comparison usage still requires:

- at least two completed run bundles from `03-04`
- any referenced PostgreSQL `backtest_run_id` rows to remain available if the operator enables PostgreSQL resolution

## Next Phase Readiness

- Phase 3 now has comparison-ready run bundles, lineage manifests, and a documented reporting CLI.
- The remaining work is phase-level human verification of the real training environment and operator readability of the generated comparison reports.

---
*Phase: 03-train-the-model-on-1-minute-crypto-candles*
*Completed: 2026-04-16*
