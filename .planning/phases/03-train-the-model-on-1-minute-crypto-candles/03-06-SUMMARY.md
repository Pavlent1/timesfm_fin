---
phase: 03-train-the-model-on-1-minute-crypto-candles
plan: "06"
subsystem: training
tags: [timesfm, training, btcusdt, rerun, short-horizon]
requires:
  - phase: 03-train-the-model-on-1-minute-crypto-candles
    provides: manual wrapper, prepared-bundle workflow, lineage reporting
provides:
  - short-horizon legacy-training shape support
  - dense stride-1 BTC rerun artifacts
  - comparison-ready local-checkpoint backtest report
affects: [phase-03-training, reproducibility, evaluation]
tech-stack:
  added: []
  patterns: [validated training-shape contract, dense BTC rerun, file-first comparison artifacts]
key-files:
  created:
    - src/training_shapes.py
    - AgentHelper/ProjectFiles/DescriptionFiles/src/training_shapes.py.md
    - .planning/phases/03-train-the-model-on-1-minute-crypto-candles/03-06-SUMMARY.md
  modified:
    - src/main.py
    - src/train.py
    - src/train_from_postgres.py
    - configs/fine_tuning.py
    - tests/test_training_workflow.py
    - tests/test_training_preparer.py
    - README.md
key-decisions:
  - "The legacy training path now treats `output_len == horizon_len` and `window_length == context_len + output_len` as explicit validated requirements instead of silent 128-step assumptions."
  - "The one-month BTC rerun uses `window_length = 517` and `stride = 1` so the bundle matches the 5-step objective while staying dense."
  - "The rerun stayed on `batch_size = 1` because that is the only proven-safe VRAM setting on this RTX 4070 Laptop GPU path."
patterns-established:
  - "Short-horizon reruns can come from either a dedicated config file or `train_from_postgres.py` shape overrides, and the effective shape is always recorded in `run_manifest.json`."
  - "Comparison-friendly text reports for fine-tuned checkpoints continue to flow through `src/crypto_minute_backtest.py` with the same report shape as `run_14.txt`."
requirements-completed: [MODEL-01, OPS-01]
completed: 2026-04-17
---

# Phase 03 Plan 06: Short-Horizon BTC Rerun Summary

**Dense stride-1 BTC rerun with a 5-step training objective and a `run_14`-shaped local-checkpoint report**

## Outcomes

- Added `src/training_shapes.py` and wired it through `src/main.py`, `src/train.py`, and `src/train_from_postgres.py` so the legacy trainer stops silently assuming `128/128` and instead validates the effective shape before training starts.
- Locked the new contract with targeted tests in `tests/test_training_workflow.py` and `tests/test_training_preparer.py`, including dense `stride = 1` sample counts and clear rejection of incompatible output/horizon settings.
- Regenerated the BTC-only one-month bundle with `window_length = 517` and `stride = 1`, producing `39,804` train windows under `outputs/prepared_btc_one_month_h5_stride1/` with manifest id `99a4d436f706c97a`.
- Completed a real Linux/Docker rerun at `outputs/training_runs/runs/btc-one-month-h5-s1-1ep-b1/` using the cached local parent checkpoint and produced a fine-tuned checkpoint at `checkpoints/fine-tuning-20260416-213724`.
- Generated a new local-checkpoint text backtest at `outputs/backtests/btc-one-month-h5-s1-1ep-b1-h5.txt` using the exact `run_14.txt` comparison shape: `2026-03-13` for `30` days, `horizon_len = 5`, `stride = 5`.

## Validation

- Local code validation passed before the rerun: `node scripts/precommit-checks.mjs` (`103 passed`).
- Dense bundle metadata confirms the requested shape:
  - `window_length = 517`
  - `stride = 1`
  - `sample_counts.total = 39804`
- The completed run manifest records the effective short-horizon training shape:
  - `context_len = 512`
  - `output_len = 5`
  - `horizon_len = 5`
  - `output_patch_len = 128`
  - `effective_batch_size = 1`
- Holdout evaluation summary at `outputs/training_runs/runs/btc-one-month-h5-s1-1ep-b1/evaluation_summary.json`:
  - `window_count = 8825`
  - `MAE = 64.1824`
  - `RMSE = 95.1358`
  - `MAPE = 0.0921%`
- Comparison report against `outputs/backtests/run_14.txt`:
  - Step 0 avg normalized deviation improved by `0.000261` percentage points.
  - Step 1 improved by `0.000286`.
  - Step 2 improved by `0.000107`.
  - Step 3 improved by `0.000011`.
  - Step 4 worsened slightly by `0.000101`.
  - Direction-above/below-last-input accuracy was slightly lower on steps `0` through `3`, but slightly higher on step `4`.

## Operational Notes

- The first run attempt failed because `num_epochs = 1` with `warmup_epochs = 1` makes the Pax cosine schedule degenerate (`0 must be < 0`). The run-local config was corrected to `warmup_epochs = 0` and the rerun then completed successfully.
- The legacy trainer counts epochs from `0`, so a run configured with `num_epochs = 1` still logs `Epoch 0` and `Epoch 1` before exiting on the next boundary. That is an inherited trainer quirk, not a summary typo.
- The CUDA/TensorFlow library warnings and the checkpoint-structure warnings were non-blocking in this runtime. JAX still used the CUDA device, the checkpoint restored, and the run produced the expected artifacts.
