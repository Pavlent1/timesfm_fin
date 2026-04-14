from __future__ import annotations


def test_bootstrap_schema_creates_required_phase1_tables(
    bootstrapped_postgres_connection,
) -> None:
    expected_tables = {
        "market_data.assets",
        "market_data.series",
        "market_data.ingestion_runs",
        "market_data.observations",
    }

    rows = bootstrapped_postgres_connection.execute(
        """
        SELECT schemaname || '.' || tablename
        FROM pg_tables
        WHERE schemaname = 'market_data'
        """
    ).fetchall()

    actual_tables = {row[0] for row in rows}

    assert expected_tables.issubset(actual_tables)


def test_observations_store_double_precision_with_a_future_upsert_key(
    bootstrapped_postgres_connection,
) -> None:
    close_price_type = bootstrapped_postgres_connection.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'market_data'
          AND table_name = 'observations'
          AND column_name = 'close_price'
        """
    ).fetchone()[0]
    pk_columns = bootstrapped_postgres_connection.execute(
        """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_class t ON t.oid = i.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
        WHERE n.nspname = 'market_data'
          AND t.relname = 'observations'
          AND i.indisprimary
        ORDER BY array_position(i.indkey, a.attnum)
        """
    ).fetchall()

    assert close_price_type == "double precision"
    assert [row[0] for row in pk_columns] == ["series_id", "observation_time_utc"]
