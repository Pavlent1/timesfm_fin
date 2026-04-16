# `src/compare_training_runs.py`

Phase 3 cross-run comparison CLI for completed manual training bundles.

Key responsibilities:

- read two or more run directories and normalize them through `src/training_lineage.py`
- emit machine-readable `comparison_summary.json` plus operator-readable `comparison_summary.md`
- highlight parent checkpoint, prepared-bundle identity, holdout ranges, evaluation metrics, and referenced backtest ids across runs
- optionally resolve referenced PostgreSQL backtest step stats for richer comparison context

Important interactions:

- depends on `src/training_lineage.py` for per-run validation and normalization
- can reuse PostgreSQL backtest metadata through `src/postgres_backtest.py` and `src/postgres_dataset.py`
- is documented in `README.md` as the manual Phase 3 reporting step

Category: Phase 3 run comparison/reporting entrypoint.
