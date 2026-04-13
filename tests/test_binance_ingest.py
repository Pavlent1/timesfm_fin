from __future__ import annotations

from datetime import datetime, timezone

from postgres_ingest_binance import (
    default_end_utc,
    ingest_binance_rows,
    parse_args,
    run_ingest,
)


def sample_binance_rows() -> list[list]:
    return [
        [1711929600000, "70000.0", "70100.0", "69950.0", "70010.0", "1.2", 1711929659999, "0", 10, "0", "0", "0"],
        [1711929660000, "70010.0", "70120.0", "70000.0", "70050.0", "1.3", 1711929719999, "0", 11, "0", "0", "0"],
        [1711929720000, "70050.0", "70130.0", "70040.0", "70090.0", "1.1", 1711929779999, "0", 9, "0", "0", "0"],
    ]


def test_default_ingest_command_targets_btcusdt_last_year(postgres_test_database, monkeypatch) -> None:
    captured: dict[str, object] = {}

    with connect_and_bootstrap(postgres_test_database):
        args = parse_args([])
        args.host = postgres_test_database.host
        args.port = postgres_test_database.port
        args.db_name = postgres_test_database.db_name
        args.user = postgres_test_database.user
        args.password = postgres_test_database.password

        def fake_fetcher(symbol: str, start_ms: int, end_ms: int, interval: str) -> list[list]:
            captured["symbol"] = symbol
            captured["interval"] = interval
            captured["start_ms"] = start_ms
            captured["end_ms"] = end_ms
            return sample_binance_rows()

        now = datetime(2026, 4, 13, 16, 0, tzinfo=timezone.utc)
        result = run_ingest(args, fetcher=fake_fetcher, now=now)

    assert captured["symbol"] == "BTCUSDT"
    assert captured["interval"] == "1m"
    assert captured["end_ms"] == int(default_end_utc(now=now).timestamp() * 1000)
    assert captured["start_ms"] == int((default_end_utc(now=now).timestamp() - 365 * 24 * 60 * 60) * 1000)
    assert result["rows_written"] == 3


def test_rerunning_ingest_keeps_one_observation_per_timestamp(
    bootstrapped_postgres_connection,
) -> None:
    requested_start = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    requested_end = datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc)
    rows = sample_binance_rows()

    first_result = ingest_binance_rows(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
        requested_start_utc=requested_start,
        requested_end_utc=requested_end,
        rows=rows,
    )
    second_result = ingest_binance_rows(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
        requested_start_utc=requested_start,
        requested_end_utc=requested_end,
        rows=rows,
    )

    stored_rows = bootstrapped_postgres_connection.execute(
        "SELECT COUNT(*) FROM market_data.observations"
    ).fetchone()[0]

    assert first_result["rows_written"] == 3
    assert second_result["rows_written"] == 3
    assert stored_rows == 3


def connect_and_bootstrap(settings):
    from postgres_dataset import bootstrap_schema, connect_postgres

    class BootstrappedConnection:
        def __enter__(self):
            self.conn = connect_postgres(settings=settings, autocommit=False)
            bootstrap_schema(self.conn)
            return self.conn

        def __exit__(self, exc_type, exc, tb):
            self.conn.close()

    return BootstrappedConnection()
