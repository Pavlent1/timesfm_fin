# `src/postgres_ingest_binance.py`

CLI and core workflow for loading Binance close-price candles into the Phase 1 PostgreSQL schema.

Key responsibilities:

- parse the one-shot PostgreSQL ingest command, defaulting to `BTCUSDT`, `1m`, and the last 365 days
- build reusable ingest argument namespaces for higher-level workflows that still need the same canonical Binance-to-PostgreSQL path
- compute the requested UTC range when the caller does not pass explicit start and end times
- fetch Binance klines through `src/binance_market_data.py`
- create or reuse logical series rows, record ingestion provenance, and upsert observations into PostgreSQL
- print a short ingest summary for CLI operators

Important interactions:

- imports shared PostgreSQL helpers from `src/postgres_dataset.py`
- shares the extracted Binance pagination path with `src/crypto_minute_backtest.py`
- is reused by `src/postgres_prepare_training_source.py` so Phase 3 source backfill does not fork a second storage flow

Category: PostgreSQL ingestion entrypoint.
