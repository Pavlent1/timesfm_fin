# `src/bootstrap_postgres.py`

Operator-facing CLI for applying the checked-in Phase 1 PostgreSQL schema to a target database.

Key responsibilities:

- parse host, port, database, user, password, and schema-file arguments
- wait for PostgreSQL readiness unless the caller opts out
- connect through `src/postgres_dataset.py`
- apply `db/init/001_phase1_schema.sql` without manual SQL editing
- print the target database that was bootstrapped

Important interactions:

- imports `PostgresSettings`, `connect_postgres()`, `wait_for_postgres()`, and `bootstrap_schema()` from `src/postgres_dataset.py`
- is intended to complement the Docker Compose init mount, not replace the checked-in schema source of truth

Category: PostgreSQL bootstrap entrypoint.
