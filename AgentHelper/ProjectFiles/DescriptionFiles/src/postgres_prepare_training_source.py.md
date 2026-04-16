# `src/postgres_prepare_training_source.py`

Manual Phase 3 source-readiness CLI for backfilling and verifying the approved training symbols in PostgreSQL.

Key responsibilities:

- enforce the Phase 3 symbol allowlist of `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`
- map those symbols to the approved source-coverage targets of 40 BTC months and 36 ETH/SOL months
- reuse `src/postgres_ingest_binance.py` to backfill the canonical PostgreSQL store instead of creating a training-only ingest path
- evaluate whether each symbol is training-ready, including whether Bitcoin can still reserve the latest four months for backtests
- fail fast when PostgreSQL coverage is missing, too short, or contains blocking minute-gap segments

Important interactions:

- uses PostgreSQL connection settings from `src/postgres_dataset.py`
- reuses the ingest runner contract from `src/postgres_ingest_binance.py`
- consumes machine-readable integrity results from `src/postgres_verify_data.py`

Category: Phase 3 source readiness CLI.
