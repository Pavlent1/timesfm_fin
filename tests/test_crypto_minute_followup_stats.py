from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import crypto_minute_followup_stats


def build_analysis_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open_time_utc": pd.date_range(
                "2024-04-01T00:00:00Z",
                periods=10,
                freq="1min",
                tz="UTC",
            ),
            "close": np.arange(1.0, 11.0, dtype=np.float64),
        }
    )


def test_load_analysis_frame_includes_one_candle_lookback_for_requested_day(
    bootstrapped_postgres_connection,
    dataset_factory,
) -> None:
    conn = bootstrapped_postgres_connection
    series_id = dataset_factory.ensure_series(
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
    )
    ingestion_run_id = dataset_factory.create_ingestion_run(
        series_id=series_id,
        requested_start_utc=datetime(2024, 3, 31, 23, 59, tzinfo=timezone.utc),
        requested_end_utc=datetime(2024, 4, 1, 0, 4, tzinfo=timezone.utc),
        rows_written=5,
        status="completed",
    )
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO market_data.observations (
                series_id,
                observation_time_utc,
                close_price,
                ingestion_run_id
            )
            VALUES (%s, %s, %s, %s)
            """,
            [
                (series_id, timestamp, close_price, ingestion_run_id)
                for timestamp, close_price in [
                    (datetime(2024, 3, 31, 23, 59, tzinfo=timezone.utc), 69990.0),
                    (datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc), 70010.0),
                    (datetime(2024, 4, 1, 0, 1, tzinfo=timezone.utc), 70050.0),
                    (datetime(2024, 4, 1, 0, 2, tzinfo=timezone.utc), 70090.0),
                    (datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc), 70110.0),
                ]
            ],
        )
    conn.commit()

    frame = crypto_minute_followup_stats.load_analysis_frame(
        conn=conn,
        symbol="BTCUSDT",
        target_day=date(2024, 4, 1),
        days=1,
        lookback_candles=1,
    )

    assert frame["close"].tolist() == [69990.0, 70010.0, 70050.0, 70090.0, 70110.0]
    assert frame["open_time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist() == [
        "2024-03-31T23:59:00Z",
        "2024-04-01T00:00:00Z",
        "2024-04-01T00:01:00Z",
        "2024-04-01T00:02:00Z",
        "2024-04-01T00:03:00Z",
    ]


def test_run_followup_analysis_returns_per_step_stats() -> None:
    metrics, step_stats_rows = crypto_minute_followup_stats.run_followup_analysis(
        frame=build_analysis_frame(),
        lookback_candles=1,
        future_candles=5,
        stride=2,
        max_windows=None,
    )

    assert metrics == {
        "points": 10,
        "windows": 3,
        "lookback_candles": 1,
        "future_candles": 5,
    }
    assert len(step_stats_rows) == 5

    first_step = step_stats_rows[0]
    assert first_step["step_ahead"] == 1
    assert first_step["step_count"] == 3
    assert first_step["above_count"] == 3
    assert first_step["below_count"] == 0
    assert first_step["match_count"] == 0
    assert first_step["above_pct"] == 100.0
    assert first_step["avg_close_difference"] == pytest.approx(1.0)
    assert first_step["avg_abs_close_difference"] == pytest.approx(1.0)
    assert first_step["avg_normalized_deviation_pct"] == pytest.approx(
        np.mean([50.0, 25.0, (1.0 / 6.0) * 100.0])
    )

    final_step = step_stats_rows[4]
    assert final_step["step_ahead"] == 5
    assert final_step["step_count"] == 3
    assert final_step["avg_close_difference"] == pytest.approx(5.0)
    assert final_step["avg_abs_close_difference"] == pytest.approx(5.0)


def test_render_followup_report_includes_step_stats_table() -> None:
    args = argparse.Namespace(
        symbol="BTCUSDT",
        day=date(2024, 4, 1),
        days=2,
        future_candles=5,
        stride=3,
        host="127.0.0.1",
        port=54329,
        db_name="timesfm_fin",
    )

    report = crypto_minute_followup_stats.render_followup_report(
        args=args,
        requested_start_dt=datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        requested_end_dt=datetime(2024, 4, 3, 0, 0, tzinfo=timezone.utc),
        loaded_candle_count=2881,
        evaluation_candle_count=2880,
        lookback_candle_count=1,
        metrics={
            "points": 2881,
            "windows": 960,
            "lookback_candles": 1,
            "future_candles": 5,
        },
        step_stats_rows=[
            {
                "step_ahead": 1,
                "step_count": 960,
                "above_count": 490,
                "below_count": 450,
                "match_count": 20,
                "above_pct": 51.04,
                "below_pct": 46.88,
                "match_pct": 2.08,
                "avg_close_difference": 12.5,
                "avg_abs_close_difference": 33.1,
                "avg_normalized_deviation_pct": 0.12,
                "stddev_normalized_deviation_pct": 0.03,
            }
        ],
    )

    assert "Crypto Minute Candle Follow-up Stats Report" in report
    assert "Requested days: 2" in report
    assert "Future candles per window: 5" in report
    assert "Analysis windows: 960" in report
    assert "Per-step stats" in report
    assert "avg_normalized_deviation_pct" in report
    assert "12.5" in report


def test_default_report_path_uses_symbol_day_and_future_candles() -> None:
    args = argparse.Namespace(
        symbol="BTCUSDT",
        day=date(2024, 4, 1),
        days=2,
        future_candles=5,
    )

    assert crypto_minute_followup_stats.default_report_path(args) == Path(
        "outputs/backtests/followup_stats_btcusdt_2024-04-01_2d_next5.txt"
    )
