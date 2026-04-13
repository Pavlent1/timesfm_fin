# `src/postgres_dataset.py`

Shared PostgreSQL connection and schema-bootstrap helpers for the new Phase 1 data layer.

Key responsibilities:

- load the repo-default PostgreSQL host, port, database, user, and password, with env overrides
- open psycopg connections through one shared connection path instead of per-script ad hoc DSNs
- resolve the checked-in schema SQL file under `db/init/001_phase1_schema.sql`
- wait for the compose-managed PostgreSQL service to become reachable
- apply the Phase 1 schema to a target database

Important interactions:

- `src/bootstrap_postgres.py` uses these helpers for the operator-facing bootstrap CLI
- later PostgreSQL CLIs should import `connect_postgres()` from here instead of rebuilding connection logic
- the Phase 1 pytest fixtures reuse the same helpers to validate the database contract

Category: shared PostgreSQL infrastructure.
