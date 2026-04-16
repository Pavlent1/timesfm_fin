---
phase: 03-train-the-model-on-1-minute-crypto-candles
plan: "04"
subsystem: training
tags: [timesfm, training, lineage, holdout]
requires:
  - phase: 03-train-the-model-on-1-minute-crypto-candles
    provides: prepared bundle contract and frozen training environment
provides:
  - manual training wrapper for prepared PostgreSQL bundles
  - explicit holdout evaluation and holdout backtest adapters
  - deterministic run-bundle metadata for later lineage reporting
affects: [phase-03-training, reproducibility, evaluation]
tech-stack:
  added: []
  patterns: [deterministic run bundles, explicit parent checkpoint selection, holdout-first reporting]
key-files:
  created:
    - src/train_from_postgres.py
    - src/evaluate_training_run.py
    - src/backtest_training_run.py
    - AgentHelper/ProjectFiles/DescriptionFiles/src/train_from_postgres.py.md
    - AgentHelper/ProjectFiles/DescriptionFiles/src/evaluate_training_run.py.md
    - AgentHelper/ProjectFiles/DescriptionFiles/src/backtest_training_run.py.md
  modified:
    - src/main.py
    - tests/test_training_workflow.py
    - AgentHelper/ProjectFiles/DescriptionFiles/src/main.py.md
key-decisions:
  - "The manual wrapper requires an explicit parent checkpoint path or repo id and never inherits src/main.py's silent Google default."
  - "The trainer's internal shuffled eval is non-canonical for Phase 3; real comparison inputs are evaluation_summary.json and backtest_summary.json from the explicit holdout artifact."
patterns-established:
  - "Prepared bundle sample counts must be used to derive a compatible copied config before training starts."
  - "Manual Phase 3 runs write one deterministic run bundle containing copied config, environment snapshot, evaluation summary, and backtest summary."
requirements-completed: [MODEL-01]
duration: 52 min
completed: 2026-04-16
---

# Phase 03 Plan 04: Manual Training Workflow Summary

**Explicit-parent manual training wrapper plus canonical holdout evaluation and backtest outputs**

## Performance

- **Duration:** 52 min
- **Started:** 2026-04-16T14:29:00Z
- **Completed:** 2026-04-16T15:21:00Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Extended `tests/test_training_workflow.py` so the Phase 3 wrapper contract is locked before runtime changes, including explicit parent checkpoint capture, copied config batch-size adjustment, deterministic run directories, and canonical post-train artifacts.
- Added `src/train_from_postgres.py` as the manual Phase 3 entrypoint that validates prepared bundle sample counts, copies a compatible config, captures environment metadata, invokes `src/main.py`, and writes a deterministic `run_manifest.json`.
- Added `src/evaluate_training_run.py` and `src/backtest_training_run.py` so every completed run can emit explicit `evaluation_summary.json` and `backtest_summary.json` outputs from the prepared holdout artifact instead of relying on the trainer's internal shuffled eval.
- Updated `src/main.py` to accept either `--checkpoint_path` or `--checkpoint_repo_id` from the wrapper and kept the older fallback only for direct legacy usage.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the manual training wrapper tests** - `cd5b469` (test)
2. **Task 2: Implement the manual PostgreSQL-bundle training wrapper** - `c4d822a` (feat)
3. **Task 3: Implement the post-train evaluation and backtest adapters** - `1bfb7c5` (feat)

**Plan metadata:** completed

## Files Created/Modified

- `tests/test_training_workflow.py` - Locks the manual wrapper, explicit parent checkpoint, copied-config batch-size, and post-train summary contract.
- `src/train_from_postgres.py` - Manual wrapper that turns a prepared bundle into a deterministic Phase 3 run bundle.
- `src/evaluate_training_run.py` - Explicit holdout evaluator that writes `evaluation_summary.json`.
- `src/backtest_training_run.py` - Explicit holdout backtest adapter that writes `backtest_summary.json`.
- `src/main.py` - Accepts explicit parent checkpoint repo ids in addition to local checkpoint paths.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/train_from_postgres.py.md` - Mirrors the wrapper responsibility.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/evaluate_training_run.py.md` - Mirrors the explicit holdout evaluation responsibility.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/backtest_training_run.py.md` - Mirrors the explicit holdout backtest responsibility.
- `AgentHelper/ProjectFiles/DescriptionFiles/src/main.py.md` - Records the new explicit parent-checkpoint behavior.

## Decisions Made

- Made parent checkpoint selection explicit at the wrapper boundary so later lineage and comparisons stay interpretable across repo-id and local-path parents.
- Treated the prepared bundle's sample-count metadata as the source of truth for copied config adjustment so the one-month starter run cannot silently collapse to `train_size=0`.
- Chose file-based `evaluation_summary.json` and `backtest_summary.json` artifacts as the canonical Phase 3 comparison inputs for later reporting.

## Deviations from Plan

### Auto-fixed Issues

**1. Existing environment snapshot helper already covered the wrapper metadata needs**
- **Found during:** Task 2 (Implement the manual PostgreSQL-bundle training wrapper)
- **Issue:** The plan listed `src/training_environment.py` as a likely touch-point, but the current helper already captured the required requirements hash, bundle identity, config path, command, package snapshot, and git commit.
- **Fix:** Reused the existing helper unchanged and captured the additional wrapper-level metadata in `run_manifest.json` instead of adding a redundant second snapshot format.
- **Files modified:** `src/train_from_postgres.py`
- **Verification:** `.\.venv\Scripts\python.exe -m pytest -q tests/test_training_workflow.py -x`
- **Committed in:** `c4d822a`

---

**Total deviations:** 1 auto-fixed (0 blocking)
**Impact on plan:** No scope creep. The wrapper reuses the Phase 03 environment contract instead of forking it.

## Issues Encountered

None.

## User Setup Required

Real training execution still requires:

- a prepared PostgreSQL-derived bundle from `03-02`
- a supported TimesFM v1 training environment matching `requirements.training.txt`
- an explicit parent checkpoint path or repo id supplied by the operator

## Next Phase Readiness

- Phase 3 runs now produce deterministic bundle metadata plus explicit holdout evaluation and backtest artifacts.
- Plan `03-05` can normalize those run bundles into lineage manifests and cross-run comparison reports without reverse-engineering checkpoint folders.

---
*Phase: 03-train-the-model-on-1-minute-crypto-candles*
*Completed: 2026-04-16*
