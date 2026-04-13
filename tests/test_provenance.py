from __future__ import annotations

from datetime import datetime, timezone

from postgres_ingest_binance import ingest_binance_rows


def sample_binance_rows() -> list[list]:
    return [
        [1711929600000, "70000.0", "70100.0", "69950.0", "70010.0", "1.2", 1711929659999, "0", 10, "0", "0", "0"],
        [1711929660000, "70010.0", "70120.0", "70000.0", "70050.0", "1.3", 1711929719999, "0", 11, "0", "0", "0"],
        [1711929720000, "70050.0", "70130.0", "70040.0", "70090.0", "1.1", 1711929779999, "0", 9, "0", "0", "0"],
    ]


def test_ingestion_run_records_source_range_and_completion_metadata(
    bootstrapped_postgres_connection,
) -> None:
    requested_start = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    requested_end = datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc)

    result = ingest_binance_rows(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
        requested_start_utc=requested_start,
        requested_end_utc=requested_end,
        rows=sample_binance_rows(),
    )

    row = bootstrapped_postgres_connection.execute(
        """
        SELECT
            source_endpoint,
            requested_start_utc,
            requested_end_utc,
            actual_start_utc,
            actual_end_utc,
            rows_written,
            status,
            completed_at_utc,
            notes->>'symbol',
            notes->>'timeframe'
        FROM market_data.ingestion_runs
        WHERE ingestion_run_id = %s
        """,
        (result["ingestion_run_id"],),
    ).fetchone()

    assert row[0] == "https://api.binance.com/api/v3/klines"
    assert row[1] == requested_start
    assert row[2] == requested_end
    assert row[3] == datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    assert row[4] == datetime(2024, 4, 1, 0, 2, tzinfo=timezone.utc)
    assert row[5] == 3
    assert row[6] == "completed"
    assert row[7] is not None
    assert row[8] == "BTCUSDT"
    assert row[9] == "1m"
