# `src/postgres_prepare_training.py`

Phase 3 PostgreSQL cleaner and bundle preparer for manifest-selected training slices.

Key responsibilities:

- load explicit per-symbol train and holdout slices from PostgreSQL using the manifest contract
- enforce strict or repair-capable cleaning over minute gaps before any model bundle is emitted
- materialize fixed-length training windows that match the current TimesFM `512 + 128` sample shape
- write bundle sidecars such as `dataset_manifest.json`, `quality_report.json`, `holdout_series.csv`, and `window_index.csv`
- publish machine-readable per-symbol and total sample counts for later training-viability checks

Important interactions:

- consumes explicit slice and cleaning settings from `src/training_manifest.py`
- reuses PostgreSQL observation loading from `src/postgres_verify_data.py`
- emits the prepared bundle artifacts that later training workflow code can pass to `src/main.py`

Category: Phase 3 training bundle preparer.
