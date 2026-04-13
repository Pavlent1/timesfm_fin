# PostgreSQL Phase 1 Schema

This repository now includes a single repo-owned PostgreSQL workflow for local dataset setup, ingestion, discovery, verification, and CSV materialization.

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

## Notes

- The local development trust boundary is the compose-managed PostgreSQL service plus the Python CLIs in `src/`.
- Keep secrets local. The checked-in defaults are for development only.
- `/docker-entrypoint-initdb.d/001_phase1_schema.sql` is the schema source of truth for first boot, and `src/bootstrap_postgres.py` is the re-apply path for an existing database.
