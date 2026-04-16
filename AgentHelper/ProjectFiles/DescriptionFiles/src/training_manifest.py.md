# `src/training_manifest.py`

Canonical Phase 3 manifest contract for selecting explicit PostgreSQL train and holdout slices.

Key responsibilities:

- enforce the approved Phase 3 symbol scope of `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`
- validate per-symbol train and holdout timestamps, including inverted or overlapping ranges
- expose the starter one-month-per-symbol preset while keeping custom explicit slices as the canonical contract
- serialize manifests as stable JSON that later preparation and training workflows can reuse
- provide a reproducibility-friendly manifest identity derived from the normalized payload

Important interactions:

- feeds explicit slice and cleaning choices into `src/postgres_prepare_training.py`
- aligns the emitted window and stride defaults with the current TimesFM training expectations

Category: Phase 3 manifest contract.
