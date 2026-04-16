# `src/evaluate_training_run.py`

Phase 3 explicit holdout evaluator for trained checkpoints.

Key responsibilities:

- load the prepared bundle's explicit `holdout_series.csv`
- build context/horizon windows from that holdout artifact instead of relying on the legacy trainer's shuffled eval split
- forecast those windows with either a local checkpoint path or a repo id
- compute canonical holdout metrics such as MAE, RMSE, and MAPE
- write `evaluation_summary.json` for later lineage and comparison steps

Important interactions:

- consumes the holdout artifact emitted by `src/postgres_prepare_training.py`
- can load the same TimesFM checkpoint family as the forecasting scripts
- is called by `src/train_from_postgres.py`
- supplies normalized per-symbol and overall holdout metrics to `src/training_lineage.py`

Category: Phase 3 holdout evaluation adapter.
