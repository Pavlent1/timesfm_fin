---
phase: 03-train-the-model-on-1-minute-crypto-candles
plan: "02"
subsystem: database
tags: [postgresql, manifest, dataset, training]
requires:
  - phase: 03-train-the-model-on-1-minute-crypto-candles
    provides: source-readiness CLI and segment-aware integrity output
provides:
  - manifest contract for explicit train and holdout slices
  - PostgreSQL cleaner and bundle preparer for fixed-length training windows
  - machine-readable dataset and quality sidecars for later training workflows
affects: [phase-03-training, holdouts, reproducibility]
tech-stack:
  added: []
  patterns: [manifest-first bundle preparation, strict-vs-repair cleaning]
key-files:
  created:
    - src/training_manifest.py
    - src/postgres_prepare_training.py
    - tests/test_training_manifest.py
    - tests/test_training_preparer.py
    - AgentHelper/ProjectFiles/DescriptionFiles/src/training_manifest.py.md
    - AgentHelper/ProjectFiles/DescriptionFiles/src/postgres_prepare_training.py.md
  modified: []
key-decisions:
  - "Manifest JSON is now the canonical source of truth for per-symbol train and holdout slices."
  - "Prepared training bundles emit fixed-length 640-point windows plus explicit holdout and quality sidecars instead of reusing the older aligned-matrix export."
patterns-established:
  - "Phase 3 bundle preparation validates manifest slices before touching PostgreSQL."
  - "Training-prep outputs must include sample counts, quality reporting, and explicit holdout artifacts."
requirements-completed: [MODEL-01, MODEL-02]
duration: 4 min
completed: 2026-04-16
---

# Phase 03 Plan 02: Bundle Preparation Summary

**Manifest-driven PostgreSQL training-bundle preparer with explicit holdouts, strict-versus-repair cleaning, and 640-point window emission**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-16T13:51:57Z
- **Completed:** 2026-04-16T13:56:25Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added `src/training_manifest.py` so Phase 3 can lock explicit per-symbol train and holdout slices in one canonical manifest.
- Added `src/postgres_prepare_training.py` to clean PostgreSQL minute data, repair short gaps when allowed, and emit fixed-length 640-point train windows plus holdout artifacts.
- Locked the preparation contract with new manifest and preparer tests that cover invalid slices, starter presets, strict-versus-repair behavior, and machine-readable sample counts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write manifest and preparer contract tests** - `e8afb68` (test)
2. **Task 2: Implement the manifest contract for per-symbol ranges and holdouts** - `44e23c5` (feat)
3. **Task 3: Implement the PostgreSQL cleaner and fixed-window bundle preparer** - `fec3461` (feat)

**Plan metadata:** pending

## Files Created/Modified

- `tests/test_training_manifest.py` - Defines the manifest contract, preset behavior, and serialization expectations.
- `tests/test_training_preparer.py` - Verifies strict and repair bundle preparation from PostgreSQL-backed data.
- `src/training_manifest.py` - Validates, builds, loads, and writes the canonical Phase 3 slice manifest.
- `src/postgres_prepare_training.py` - Materializes prepared training bundles and sidecar artifacts from PostgreSQL observations.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/training_manifest.py.md` - Mirrors the new manifest contract responsibility.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/postgres_prepare_training.py.md` - Mirrors the new bundle-preparer responsibility.

## Decisions Made

- Chose a manifest-first contract so later training runs can point back to one stable JSON record of symbol slices, cleaning settings, and window defaults.
- Emitted `train_windows.csv`, `holdout_series.csv`, `dataset_manifest.json`, `quality_report.json`, and `window_index.csv` as the canonical prepared-bundle shape instead of overloading the older `training_matrix` export.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no additional external service configuration required beyond the Phase 03 setup already captured in `03-USER-SETUP.md`.

## Next Phase Readiness

- Phase 3 now has a reproducible bundle contract with explicit train/holdout slices, repair tracking, and sample counts for downstream viability checks.
- Plan `03-03` can freeze the training environment and capture run metadata against a concrete prepared-bundle shape instead of an implicit CSV convention.

---
*Phase: 03-train-the-model-on-1-minute-crypto-candles*
*Completed: 2026-04-16*
