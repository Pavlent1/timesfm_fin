# `src/backtest_training_run.py`

Phase 3 holdout backtest adapter for trained checkpoints.

Key responsibilities:

- read the prepared bundle's explicit holdout artifact
- run rolling forecast windows against the trained checkpoint using Phase 2 metric semantics from `src/backtest_metrics.py`
- aggregate per-step normalized deviation and direction-guess stats into a file-based summary
- record `backtest_run_id` values only as supplemental provenance when a caller persists results externally
- write `backtest_summary.json` for lineage and cross-run comparison

Important interactions:

- reuses holdout loading and window construction behavior from `src/evaluate_training_run.py`
- reuses step-metric formulas from `src/backtest_metrics.py`
- is called by `src/train_from_postgres.py`
- feeds comparison-ready backtest summary artifacts into `src/training_lineage.py`

Category: Phase 3 holdout backtest adapter.
