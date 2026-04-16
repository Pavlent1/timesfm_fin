# `src/training_environment.py`

Phase 3 reproducibility helper for capturing the effective manual training environment.

Key responsibilities:

- read the frozen `requirements.training.txt` input and record its hash
- capture Python version, Python executable, package snapshot, and git commit for a manual run
- attach the copied training config path and prepared-bundle manifest identity to one environment snapshot
- write the snapshot as stable JSON for later wrapper and lineage steps to reuse
- keep the workflow explicitly manual-only instead of introducing any scheduler or background orchestration

Important interactions:

- pairs with `requirements.training.txt` as the frozen environment input
- records the prepared-bundle manifest identity emitted by `src/postgres_prepare_training.py`
- is designed for later reuse by the Phase 3 wrapper and comparison steps

Category: Phase 3 environment snapshot helper.
