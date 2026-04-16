# `src/train_from_postgres.py`

Phase 3 manual training wrapper for launching the legacy TimesFM v1 trainer from
prepared PostgreSQL-derived bundles.

Key responsibilities:

- validate the prepared bundle contract before training starts
- require an explicit parent checkpoint path or repo id and record that choice
- derive a bundle-compatible batch size so the legacy train/eval split does not collapse to zero
- copy the training config into a deterministic run directory and capture the environment snapshot
- invoke `src/main.py` without replacing the underlying training engine
- write `run_manifest.json`, then attach canonical `evaluation_summary.json` and `backtest_summary.json`

Important interactions:

- consumes `dataset_manifest.json`, `train_windows.csv`, and `holdout_series.csv` emitted by `src/postgres_prepare_training.py`
- reuses environment capture helpers from `src/training_environment.py`
- delegates explicit holdout evaluation to `src/evaluate_training_run.py`
- delegates holdout backtest summarization to `src/backtest_training_run.py`
- passes either `--checkpoint_path` or `--checkpoint_repo_id` into `src/main.py`

Category: Phase 3 manual training workflow entrypoint.
