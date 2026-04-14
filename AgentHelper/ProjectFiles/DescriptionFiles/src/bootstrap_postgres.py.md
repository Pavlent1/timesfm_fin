# `src/bootstrap_postgres.py`

Operator-facing CLI for applying the checked-in PostgreSQL schema set to a target database.

Key responsibilities:

- parse host, port, database, user, password, and schema anchor arguments
- wait for PostgreSQL readiness unless the caller opts out
- connect through `src/postgres_dataset.py`
- hand the checked-in schema anchor path to `bootstrap_schema()`, which now applies all sibling `db/init/*.sql` files in lexical order
- print the target database that was bootstrapped

Important interactions:

- imports `PostgresSettings`, `connect_postgres()`, `default_schema_path()`, `load_postgres_settings()`, `wait_for_postgres()`, and `bootstrap_schema()` from `src/postgres_dataset.py`
- stays aligned with the checked-in `db/init/` bootstrap path rather than embedding schema SQL inline

Category: PostgreSQL bootstrap entrypoint.
