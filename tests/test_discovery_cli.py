from __future__ import annotations

from datetime import datetime, timedelta, timezone

from postgres_dataset import (
    ensure_series,
    finalize_ingestion_run,
    start_ingestion_run,
    upsert_observations,
)
from postgres_discover_data import discover_series, render_discovery_table
from postgres_verify_data import build_integrity_report, render_integrity_report


def seed_series(
    conn,
    *,
    symbol: str,
    source_name: str,
    timeframe: str,
    observations: list[tuple[datetime, float]],
) -> None:
    series_id = ensure_series(
        conn=conn,
        symbol=symbol,
        source_name=source_name,
        timeframe=timeframe,
    )
    ingestion_run_id = start_ingestion_run(
        conn=conn,
        series_id=series_id,
        source_endpoint="seed://test",
        requested_start_utc=observations[0][0],
        requested_end_utc=observations[-1][0] + timedelta(minutes=1),
        notes={"seeded": True},
    )
    rows_written = upsert_observations(
        conn=conn,
        series_id=series_id,
        ingestion_run_id=ingestion_run_id,
        observations=observations,
    )
    finalize_ingestion_run(
        conn=conn,
        ingestion_run_id=ingestion_run_id,
        actual_start_utc=observations[0][0],
        actual_end_utc=observations[-1][0],
        rows_written=rows_written,
        status="completed",
    )
    conn.commit()


def test_discovery_filters_and_sorting(bootstrapped_postgres_connection) -> None:
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    seed_series(
        bootstrapped_postgres_connection,
        symbol="SOLUSDT",
        source_name="binance",
        timeframe="1m",
        observations=[
            (base, 180.0),
            (base + timedelta(minutes=1), 181.0),
        ],
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
        observations=[
            (base, 70000.0),
            (base + timedelta(minutes=1), 70010.0),
            (base + timedelta(minutes=2), 70020.0),
        ],
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="csv_import",
        timeframe="1m",
        observations=[
            (base, 69990.0),
            (base + timedelta(minutes=1), 70005.0),
        ],
    )

    frame = discover_series(
        bootstrapped_postgres_connection,
        source="binance",
        timeframe="1m",
        sort_by="symbol",
    )
    rendered = render_discovery_table(frame)

    assert list(frame["symbol"]) == ["BTCUSDT", "SOLUSDT"]
    assert list(frame["row_count"]) == [3, 2]
    assert "BTCUSDT" in rendered
    assert "SOLUSDT" in rendered
    assert "csv_import" not in rendered


def test_integrity_report_surfaces_gap_and_minute_alignment_issues(
    bootstrapped_postgres_connection,
) -> None:
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
        observations=[
            (base, 70000.0),
            (base + timedelta(minutes=2), 70020.0),
        ],
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="ETHUSDT",
        source_name="binance",
        timeframe="1m",
        observations=[
            (base + timedelta(seconds=30), 3500.0),
            (base + timedelta(minutes=1, seconds=30), 3510.0),
        ],
    )

    report = build_integrity_report(bootstrapped_postgres_connection, source="binance")
    rendered = render_integrity_report(report)

    assert report["issue_counts"]["duplicate_timestamps"] == 0
    assert report["issue_counts"]["missing_minute_gaps"] == 1
    assert report["issue_counts"]["ordering_issues"] == 0
    assert report["issue_counts"]["null_values"] == 0
    assert report["issue_counts"]["out_of_range_timestamps"] == 2
    assert "missing_minute_gaps: 1" in rendered
    assert "out_of_range_timestamps: 2" in rendered
    assert "Coverage summary:" in rendered
