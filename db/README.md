# PostgreSQL Phase 1 + Phase 2 Schema

This repository now includes one repo-owned PostgreSQL workflow for local
dataset setup, ingestion, discovery, verification, CSV materialization, and
crypto minute backtest storage.

## Command Sequence

Start the local database:

```bash
docker compose up -d postgres
```

Apply or re-apply the checked-in schema:

```bash
python src/bootstrap_postgres.py
```

Ingest the default Binance dataset:

```bash
python src/postgres_ingest_binance.py
```

Inspect stored coverage:

```bash
python src/postgres_discover_data.py --source binance --timeframe 1m
```

Run integrity verification:

```bash
python src/postgres_verify_data.py --source binance --timeframe 1m
```

Export a forecast-ready CSV:

```bash
python src/postgres_materialize_dataset.py --mode series_csv --source binance --symbol BTCUSDT --timeframe 1m --output-csv outputs/btc_series.csv
```

Export a training matrix:

```bash
python src/postgres_materialize_dataset.py --mode training_matrix --source binance --timeframe 1m --output-csv outputs/training_matrix.csv
```

Run the PostgreSQL-backed crypto minute backtest:

```bash
python src/crypto_minute_backtest.py --day 2026-04-11 --context-len 512 --horizon-len 16 --batch-size 64
```

Inspect per-step backtest stats:

```sql
SELECT *
FROM market_data.backtest_step_stats_vw
WHERE run_id = 1
ORDER BY step_index;
```

## Tables

### `market_data.assets`

- one row per tracked asset symbol
- keeps the schema multi-asset from the start

### `market_data.series`

- one logical dataset slice per `(asset, source, timeframe, field)`
- the current Phase 1 field is `close_price`

### `market_data.ingestion_runs`

- provenance table for every load attempt
- stores requested range, actual stored range, status, row counts, and completion time

### `market_data.observations`

- one row per `(series_id, observation_time_utc)`
- stores `close_price` as `double precision`
- uniqueness on `(series_id, observation_time_utc)` enables idempotent `ON CONFLICT` upserts

### `market_data.backtest_runs`

- one row per stored backtest execution
- records the model repo, backend, frequency bucket, context/horizon settings, and source coverage window

### `market_data.backtest_windows`

- one row per forecast origin inside a stored backtest run
- tracks the target start time, the end of the context window, and the last observed input close

### `market_data.backtest_prediction_steps`

- one row per predicted horizon step for each backtest window
- stores predicted and actual closes plus the normalized deviation, signed deviation, and overshoot label locked in Phase 2

### `market_data.backtest_step_stats_vw`

- grouped SQL view over `market_data.backtest_prediction_steps`
- exposes step-level aggregate statistics for a single run without recomputing metrics in Python

## Notes

- The local development trust boundary is the compose-managed PostgreSQL service plus the Python CLIs in `src/`.
- Keep secrets local. The checked-in defaults are for development only.
- Checked-in `db/init/*.sql` files are the schema source of truth for first boot, and `src/bootstrap_postgres.py` is the re-apply path for an existing database.
