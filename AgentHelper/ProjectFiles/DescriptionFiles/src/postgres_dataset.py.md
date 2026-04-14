# `src/postgres_dataset.py`

Shared PostgreSQL connection and schema-bootstrap helpers for the PostgreSQL data layer.

Key responsibilities:

- load the repo-default PostgreSQL host, port, database, user, and password, with env overrides
- open psycopg connections through one shared connection path instead of per-script ad hoc DSNs
- resolve the checked-in schema anchor under `db/init/001_phase1_schema.sql`
- discover all checked-in `db/init/*.sql` files and apply them in lexical order during bootstrap
- wait for the compose-managed PostgreSQL service to become reachable
- apply the checked-in schema set to a target database
- create logical asset and series rows for the PostgreSQL dataset
- record and finalize ingestion-run provenance metadata
- upsert observation rows against the Phase 1 uniqueness key

Important interactions:

- `src/bootstrap_postgres.py` uses these helpers for the operator-facing bootstrap CLI
- `src/postgres_ingest_binance.py` reuses the same module for series creation, provenance tracking, and observation upserts
- `src/postgres_backtest.py` depends on this module's bootstrap path to guarantee the Phase 2 backtest tables and view exist
- later PostgreSQL CLIs should import `connect_postgres()` from here instead of rebuilding connection logic
- the Phase 1 pytest fixtures reuse the same helpers to validate the database contract

Category: shared PostgreSQL infrastructure.
