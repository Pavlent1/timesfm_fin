# `src/binance_market_data.py`

Reusable Binance REST helper module extracted from the older SQLite backtest script.

Key responsibilities:

- define the shared Binance klines endpoint constant and 1-minute interval constant
- convert Binance millisecond timestamps into UTC ISO strings
- fetch paginated kline batches with deduplication and stalled-cursor protection
- retry a request when Binance responds with HTTP `429` and a `Retry-After` header

Important interactions:

- `src/crypto_minute_backtest.py` imports the shared fetch and timestamp helpers instead of carrying a second implementation
- `src/postgres_ingest_binance.py` reuses the same pagination logic for PostgreSQL ingestion

Category: external market-data adapter.
