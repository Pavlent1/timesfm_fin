# `src/postgres_verify_data.py`

CLI and reporting helpers for Phase 1 PostgreSQL dataset integrity verification.

Key responsibilities:

- parse the same discovery-oriented filters used by the inventory CLI
- load matching observations from PostgreSQL
- compute duplicate, gap, ordering, null-value, and minute-alignment issue counts
- render both issue counts and per-series coverage summaries for operators

Important interactions:

- imports shared query helpers from `src/postgres_discover_data.py`
- validates the same observation store filled by `src/postgres_ingest_binance.py`

Category: PostgreSQL integrity CLI.
