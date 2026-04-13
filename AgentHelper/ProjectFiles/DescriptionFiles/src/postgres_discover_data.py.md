# `src/postgres_discover_data.py`

CLI and query helpers for discovering which PostgreSQL datasets currently exist in the Phase 1 schema.

Key responsibilities:

- parse source, symbol, timeframe, date-range, and sort flags for discovery runs
- query aggregated dataset inventory from `assets`, `series`, `observations`, and `ingestion_runs`
- enforce an allowlist for sort keys so CLI sorting stays deterministic and SQL-safe
- render a human-readable table showing coverage ranges and row counts

Important interactions:

- later materialization workflows can reuse the same filter dimensions exposed here
- `src/postgres_verify_data.py` reuses the query helper style for integrity checks

Category: PostgreSQL discovery CLI.
