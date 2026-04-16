# `src/training_lineage.py`

Phase 3 lineage normalizer for completed manual training run bundles.

Key responsibilities:

- validate that a run bundle is complete and contains real evaluation/backtest artifacts
- normalize produced checkpoint, parent checkpoint, prepared-bundle identity, copied config, and per-symbol train/holdout ranges
- reject incomplete or metadata-only runs before comparison proceeds
- write `lineage_manifest.json` into each run directory for later reporting

Important interactions:

- consumes `run_manifest.json`, `evaluation_summary.json`, and `backtest_summary.json` from `src/train_from_postgres.py`
- exposes the normalized per-run contract used by `src/compare_training_runs.py`

Category: Phase 3 run lineage helper.
