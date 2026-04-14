from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

import crypto_minute_backtest


class PerfectBacktestModel:
    def forecast(self, contexts, freq):
        forecasts = []
        for context in contexts:
            last_value = float(context[-1])
            forecasts.append([last_value + 1.0, last_value + 2.0])
        return np.asarray(forecasts, dtype=np.float64), None


def sample_binance_rows() -> list[list]:
    return [
        [1711929600000, "70000.0", "70100.0", "69950.0", "70010.0", "1.2", 1711929659999, "0", 10, "0", "0", "0"],
        [1711929660000, "70010.0", "70120.0", "70000.0", "70050.0", "1.3", 1711929719999, "0", 11, "0", "0", "0"],
        [1711929720000, "70050.0", "70130.0", "70040.0", "70090.0", "1.1", 1711929779999, "0", 9, "0", "0", "0"],
    ]


def build_backtest_frame() -> pd.DataFrame:
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


def test_store_and_load_candles_round_trip() -> None:
    conn = sqlite3.connect(":memory:")
    crypto_minute_backtest.ensure_schema(conn)

    with conn:
        inserted = crypto_minute_backtest.store_candles(
            conn,
            exchange="binance",
            symbol="BTCUSDT",
            interval="1m",
            rows=sample_binance_rows(),
        )

    frame = crypto_minute_backtest.load_candles(
        conn,
        exchange="binance",
        symbol="BTCUSDT",
        interval="1m",
        start_ms=1711929600000,
        end_ms=1711929780000,
    )

    assert inserted == 3
    assert frame["close"].tolist() == [70010.0, 70050.0, 70090.0]
    assert frame["open_time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist() == [
        "2024-04-01T00:00:00Z",
        "2024-04-01T00:01:00Z",
        "2024-04-01T00:02:00Z",
    ]


def test_prepare_live_frame_fetches_rows_and_keeps_requested_context(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    crypto_minute_backtest.ensure_schema(conn)
    start_dt = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc)
    observed: dict[str, object] = {}

    def fake_fetch_binance_klines(*, symbol, start_ms, end_ms, interval):
        observed["fetch"] = {
            "symbol": symbol,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "interval": interval,
        }
        return sample_binance_rows()

    monkeypatch.setattr(
        crypto_minute_backtest,
        "latest_closed_minute_bounds",
        lambda context_len: (start_dt, end_dt),
    )
    monkeypatch.setattr(
        crypto_minute_backtest,
        "fetch_binance_klines",
        fake_fetch_binance_klines,
    )

    frame, loaded_start, loaded_end = crypto_minute_backtest.prepare_live_frame(
        conn=conn,
        symbol="BTCUSDT",
        context_len=3,
    )

    assert observed["fetch"] == {
        "symbol": "BTCUSDT",
        "start_ms": int(start_dt.timestamp() * 1000),
        "end_ms": int(end_dt.timestamp() * 1000),
        "interval": "1m",
    }
    assert loaded_start == start_dt
    assert loaded_end == end_dt
    assert frame["close"].tolist() == [70010.0, 70050.0, 70090.0]


def test_run_backtest_returns_metrics_and_prediction_rows() -> None:
    metrics, prediction_rows = crypto_minute_backtest.run_backtest(
        model=PerfectBacktestModel(),
        frame=build_backtest_frame(),
        context_len=4,
        horizon_len=2,
        stride=2,
        batch_size=2,
        max_windows=None,
        freq=0,
    )

    assert metrics["points"] == 10
    assert metrics["windows"] == 3
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["hit_rate"] == 1.0
    assert metrics["step1_directional_accuracy"] == 1.0
    assert metrics["end_directional_accuracy"] == 1.0
    assert len(prediction_rows) == 3
    assert prediction_rows[0][4] == 5.0
    assert json.loads(prediction_rows[0][12]) == [5.0, 6.0]


def test_run_live_forecast_returns_forecast_table() -> None:
    frame = pd.DataFrame(
        {
            "open_time_utc": pd.date_range(
                "2024-04-01T00:00:00Z",
                periods=3,
                freq="1min",
                tz="UTC",
            ),
            "close": [98.0, 99.0, 100.0],
        }
    )

    forecast_df, latest_close = crypto_minute_backtest.run_live_forecast(
        model=PerfectBacktestModel(),
        frame=frame,
        horizon_len=2,
        freq=0,
    )

    assert latest_close == 100.0
    assert forecast_df["step"].tolist() == [1, 2]
    assert forecast_df["forecast_close"].tolist() == [101.0, 102.0]
    assert forecast_df["predicted_return_pct"].tolist() == pytest.approx([1.0, 2.0])


def test_save_backtest_persists_run_and_predictions() -> None:
    conn = sqlite3.connect(":memory:")
    crypto_minute_backtest.ensure_schema(conn)
    frame = build_backtest_frame()
    metrics, prediction_rows = crypto_minute_backtest.run_backtest(
        model=PerfectBacktestModel(),
        frame=frame,
        context_len=4,
        horizon_len=2,
        stride=2,
        batch_size=2,
        max_windows=1,
        freq=0,
    )
    args = argparse.Namespace(
        symbol="BTCUSDT",
        repo_id="stub/repo",
        backend="cpu",
        freq=0,
        context_len=4,
        horizon_len=2,
        stride=2,
        batch_size=2,
    )

    with conn:
        run_id = crypto_minute_backtest.save_backtest(
            conn=conn,
            args=args,
            start_dt=frame["open_time_utc"].iloc[0].to_pydatetime(),
            end_dt=frame["open_time_utc"].iloc[-1].to_pydatetime(),
            metrics=metrics,
            prediction_rows=prediction_rows,
        )

    stored_run = conn.execute(
        "SELECT symbol, windows, mae, hit_rate FROM backtest_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    stored_predictions = conn.execute(
        "SELECT COUNT(*) FROM backtest_predictions WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]

    assert stored_run == ("BTCUSDT", 1, 0.0, 1.0)
    assert stored_predictions == 1
