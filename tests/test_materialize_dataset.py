from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from postgres_dataset import (
    ensure_series,
    finalize_ingestion_run,
    start_ingestion_run,
    upsert_observations,
)
from postgres_materialize_dataset import (
    load_matching_observations,
    materialize_series_csv,
    materialize_training_matrix,
    write_materialized_csv,
)
from run_forecast import load_series_from_csv


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
        source_endpoint="seed://materialize",
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


def test_series_csv_export_matches_forecast_csv_contract(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
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

    frame = load_matching_observations(
        bootstrapped_postgres_connection,
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
    )
    output = materialize_series_csv(frame)
    output_path = tmp_path / "btc_series.csv"
    write_materialized_csv(output, output_path)

    loaded_series = load_series_from_csv(output_path, column="Close", date_column="Date")

    assert list(output.columns) == ["Date", "Close"]
    assert output["Date"].tolist() == [
        "2024-04-01T00:00:00Z",
        "2024-04-01T00:01:00Z",
        "2024-04-01T00:02:00Z",
    ]
    assert loaded_series.tolist() == [70000.0, 70010.0, 70020.0]


def test_training_matrix_export_matches_train_preprocess_shape(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
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
        symbol="SOLUSDT",
        source_name="binance",
        timeframe="1m",
        observations=[
            (base, 180.0),
            (base + timedelta(minutes=1), 181.0),
            (base + timedelta(minutes=2), 182.0),
        ],
    )

    frame = load_matching_observations(
        bootstrapped_postgres_connection,
        source="binance",
        timeframe="1m",
    )
    output = materialize_training_matrix(frame)
    output_path = tmp_path / "training_matrix.csv"
    write_materialized_csv(output, output_path)

    exported = pd.read_csv(output_path, dtype="float64")
    transposed = exported.dropna(axis=1, how="any").transpose()

    assert output.shape == (3, 2)
    assert exported.shape == (3, 2)
    assert transposed.shape == (2, 3)
    assert all(column.startswith("binance__") for column in exported.columns)
