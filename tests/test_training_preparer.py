from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from importlib import import_module

import pandas as pd
import pytest

from postgres_dataset import (
    ensure_series,
    finalize_ingestion_run,
    start_ingestion_run,
    upsert_observations,
)


pytestmark = pytest.mark.contract


def load_manifest_module():
    return pytest.importorskip("training_manifest")


def load_preparer_module():
    return pytest.importorskip("postgres_prepare_training")


def seed_series(
    conn,
    *,
    symbol: str,
    observations: list[tuple[datetime, float]],
    source_name: str = "binance",
    timeframe: str = "1m",
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
        source_endpoint="seed://training-prepare",
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


def make_minutes(
    start: datetime,
    count: int,
    *,
    base_price: float,
    skip_indices: set[int] | None = None,
) -> list[tuple[datetime, float]]:
    observations: list[tuple[datetime, float]] = []
    skipped = skip_indices or set()
    for index in range(count):
        if index in skipped:
            continue
        observations.append(
            (
                start + timedelta(minutes=index),
                base_price + float(index),
            )
        )
    return observations


@pytest.mark.integration
def test_preparer_strict_mode_rejects_ranges_with_blocking_gaps(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    manifest_module = load_manifest_module()
    preparer_module = load_preparer_module()
    start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)

    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        observations=make_minutes(
            start,
            660,
            base_price=70000.0,
            skip_indices={20, 21, 22, 23, 24, 25},
        ),
    )

    manifest = manifest_module.validate_manifest(
        {
            "source_name": "binance",
            "timeframe": "1m",
            "preset": None,
            "window_length": 640,
            "stride": 128,
            "cleaning": {"mode": "strict", "repairable_gap_minutes": 2},
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "train_start_utc": "2025-01-01T00:00:00Z",
                    "train_end_utc": "2025-01-01T11:00:00Z",
                    "holdout_start_utc": "2025-01-01T11:00:00Z",
                    "holdout_end_utc": "2025-01-01T12:00:00Z",
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="gap"):
        preparer_module.prepare_training_bundle(
            bootstrapped_postgres_connection,
            manifest,
            tmp_path / "strict_bundle",
        )


@pytest.mark.integration
def test_preparer_repair_mode_records_short_gap_repairs(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    manifest_module = load_manifest_module()
    preparer_module = load_preparer_module()
    start = datetime(2025, 2, 1, 0, 0, tzinfo=timezone.utc)

    seed_series(
        bootstrapped_postgres_connection,
        symbol="ETHUSDT",
        observations=make_minutes(
            start,
            900,
            base_price=3000.0,
            skip_indices={150, 151},
        ),
    )

    manifest = manifest_module.validate_manifest(
        {
            "source_name": "binance",
            "timeframe": "1m",
            "preset": None,
            "window_length": 640,
            "stride": 128,
            "cleaning": {"mode": "repair", "repairable_gap_minutes": 2},
            "symbols": [
                {
                    "symbol": "ETHUSDT",
                    "train_start_utc": "2025-02-01T00:00:00Z",
                    "train_end_utc": "2025-02-01T12:00:00Z",
                    "holdout_start_utc": "2025-02-01T12:00:00Z",
                    "holdout_end_utc": "2025-02-01T15:00:00Z",
                }
            ],
        }
    )

    result = preparer_module.prepare_training_bundle(
        bootstrapped_postgres_connection,
        manifest,
        tmp_path / "repair_bundle",
    )
    quality_report = json.loads(result["quality_report_path"].read_text(encoding="utf-8"))

    assert result["quality_report_path"].exists()
    assert quality_report["repairs"]
    assert quality_report["repairs"][0]["symbol"] == "ETHUSDT"
    assert quality_report["repairs"][0]["missing_minutes"] == 2


@pytest.mark.integration
def test_preparer_emits_fixed_length_positive_train_windows_and_holdout_artifacts(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    manifest_module = load_manifest_module()
    preparer_module = load_preparer_module()
    start = datetime(2025, 3, 1, 0, 0, tzinfo=timezone.utc)

    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        observations=make_minutes(start, 960, base_price=70000.0),
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="SOLUSDT",
        observations=make_minutes(start, 960, base_price=180.0),
    )

    manifest = manifest_module.validate_manifest(
        {
            "source_name": "binance",
            "timeframe": "1m",
            "preset": None,
            "window_length": 640,
            "stride": 128,
            "cleaning": {"mode": "strict", "repairable_gap_minutes": 5},
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "train_start_utc": "2025-03-01T00:00:00Z",
                    "train_end_utc": "2025-03-01T13:00:00Z",
                    "holdout_start_utc": "2025-03-01T13:00:00Z",
                    "holdout_end_utc": "2025-03-01T16:00:00Z",
                },
                {
                    "symbol": "SOLUSDT",
                    "train_start_utc": "2025-03-01T00:00:00Z",
                    "train_end_utc": "2025-03-01T13:00:00Z",
                    "holdout_start_utc": "2025-03-01T13:00:00Z",
                    "holdout_end_utc": "2025-03-01T16:00:00Z",
                },
            ],
        }
    )

    result = preparer_module.prepare_training_bundle(
        bootstrapped_postgres_connection,
        manifest,
        tmp_path / "prepared_bundle",
    )
    train_windows = pd.read_csv(result["train_windows_path"], dtype="float64")
    holdout_series = pd.read_csv(result["holdout_series_path"])
    dataset_manifest = json.loads(result["dataset_manifest_path"].read_text(encoding="utf-8"))
    window_index = pd.read_csv(result["window_index_path"])

    assert train_windows.shape[0] == 640
    assert train_windows.shape[1] >= 2
    assert (train_windows > 0).all().all()
    assert set(holdout_series["symbol"]) == {"BTCUSDT", "SOLUSDT"}
    assert dataset_manifest["sample_counts"]["total"] == train_windows.shape[1]
    assert dataset_manifest["sample_counts"]["per_symbol"]["BTCUSDT"] >= 1
    assert dataset_manifest["sample_counts"]["per_symbol"]["SOLUSDT"] >= 1
    assert dataset_manifest["stride"] == 128
    assert set(window_index["symbol"]) == {"BTCUSDT", "SOLUSDT"}


@pytest.mark.integration
def test_preparer_preserves_stride_one_and_emits_dense_window_counts(
    bootstrapped_postgres_connection,
    tmp_path,
) -> None:
    manifest_module = load_manifest_module()
    preparer_module = load_preparer_module()
    start = datetime(2025, 4, 1, 0, 0, tzinfo=timezone.utc)

    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        observations=make_minutes(start, 960, base_price=70000.0),
    )

    manifest = manifest_module.validate_manifest(
        {
            "source_name": "binance",
            "timeframe": "1m",
            "preset": None,
            "window_length": 640,
            "stride": 1,
            "cleaning": {"mode": "strict", "repairable_gap_minutes": 5},
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "train_start_utc": "2025-04-01T00:00:00Z",
                    "train_end_utc": "2025-04-01T13:00:00Z",
                    "holdout_start_utc": "2025-04-01T13:00:00Z",
                    "holdout_end_utc": "2025-04-01T16:00:00Z",
                }
            ],
        }
    )

    result = preparer_module.prepare_training_bundle(
        bootstrapped_postgres_connection,
        manifest,
        tmp_path / "dense_bundle",
    )
    dataset_manifest = json.loads(result["dataset_manifest_path"].read_text(encoding="utf-8"))
    quality_report = json.loads(result["quality_report_path"].read_text(encoding="utf-8"))
    window_index = pd.read_csv(result["window_index_path"])

    expected_windows = 780 - 640 + 1
    assert dataset_manifest["stride"] == 1
    assert quality_report["stride"] == 1
    assert dataset_manifest["sample_counts"]["total"] == expected_windows
    assert dataset_manifest["sample_counts"]["per_symbol"]["BTCUSDT"] == expected_windows
    assert len(window_index) == expected_windows
