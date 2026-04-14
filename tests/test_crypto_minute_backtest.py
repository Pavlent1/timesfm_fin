from __future__ import annotations

import argparse
from datetime import date, datetime, timezone

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
        [
            1711929600000,
            "70000.0",
            "70100.0",
            "69950.0",
            "70010.0",
            "1.2",
            1711929659999,
            "0",
            10,
            "0",
            "0",
            "0",
        ],
        [
            1711929660000,
            "70010.0",
            "70120.0",
            "70000.0",
            "70050.0",
            "1.3",
            1711929719999,
            "0",
            11,
            "0",
            "0",
            "0",
        ],
        [
            1711929720000,
            "70050.0",
            "70130.0",
            "70040.0",
            "70090.0",
            "1.1",
            1711929779999,
            "0",
            9,
            "0",
            "0",
            "0",
        ],
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


def seed_phase1_rows(conn, dataset_factory) -> None:
    series_id = dataset_factory.ensure_series(
        symbol="BTCUSDT",
        source_name="binance",
        timeframe="1m",
    )
    ingestion_run_id = dataset_factory.create_ingestion_run(
        series_id=series_id,
        requested_start_utc=datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        requested_end_utc=datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc),
        rows_written=3,
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
                (
                    series_id,
                    datetime(2024, 4, 1, 0, minute, tzinfo=timezone.utc),
                    close_price,
                    ingestion_run_id,
                )
                for minute, close_price in enumerate([70010.0, 70050.0, 70090.0])
            ],
        )
    conn.commit()


def test_load_backtest_frame_reads_requested_day_from_phase1_postgres(
    bootstrapped_postgres_connection,
    dataset_factory,
) -> None:
    conn = bootstrapped_postgres_connection
    seed_phase1_rows(conn, dataset_factory)

    frame = crypto_minute_backtest.load_backtest_frame(
        conn=conn,
        symbol="BTCUSDT",
        target_day=date(2024, 4, 1),
    )

    assert frame["close"].tolist() == [70010.0, 70050.0, 70090.0]
    assert frame["open_time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist() == [
        "2024-04-01T00:00:00Z",
        "2024-04-01T00:01:00Z",
        "2024-04-01T00:02:00Z",
    ]


def test_prepare_live_frame_persists_fetched_rows_into_postgres(
    bootstrapped_postgres_connection,
    monkeypatch,
) -> None:
    conn = bootstrapped_postgres_connection
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

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM market_data.observations")
        observation_count = cur.fetchone()[0]
        cur.execute(
            """
            SELECT status, rows_written
            FROM market_data.ingestion_runs
            ORDER BY ingestion_run_id DESC
            LIMIT 1
            """
        )
        ingestion_row = cur.fetchone()

    assert observed["fetch"] == {
        "symbol": "BTCUSDT",
        "start_ms": int(start_dt.timestamp() * 1000),
        "end_ms": int(end_dt.timestamp() * 1000),
        "interval": "1m",
    }
    assert loaded_start == start_dt
    assert loaded_end == end_dt
    assert frame["close"].tolist() == [70010.0, 70050.0, 70090.0]
    assert observation_count == 3
    assert ingestion_row == ("completed", 3)


def test_run_backtest_returns_metrics_and_window_step_records() -> None:
    metrics, window_rows = crypto_minute_backtest.run_backtest(
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
    assert len(window_rows) == 3

    first_window = window_rows[0]
    assert first_window["window_index"] == 0
    assert first_window["last_input_close"] == 4.0
    assert first_window["target_start_utc"] == pd.Timestamp("2024-04-01T00:04:00Z")
    assert len(first_window["steps"]) == 2
    assert first_window["steps"][0] == {
        "step_index": 0,
        "target_time_utc": pd.Timestamp("2024-04-01T00:04:00Z"),
        "last_input_close": 4.0,
        "predicted_close": 5.0,
        "actual_close": 5.0,
        "normalized_deviation_pct": 0.0,
        "signed_deviation_pct": 0.0,
        "overshoot_label": "match",
    }
    assert first_window["steps"][1]["target_time_utc"] == pd.Timestamp(
        "2024-04-01T00:05:00Z"
    )


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


def test_save_backtest_writes_run_window_and_step_rows(
    bootstrapped_postgres_connection,
) -> None:
    conn = bootstrapped_postgres_connection
    frame = build_backtest_frame()
    metrics, window_rows = crypto_minute_backtest.run_backtest(
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

    run_id = crypto_minute_backtest.save_backtest(
        conn=conn,
        args=args,
        start_dt=frame["open_time_utc"].iloc[0].to_pydatetime(),
        end_dt=frame["open_time_utc"].iloc[-1].to_pydatetime(),
        metrics=metrics,
        window_rows=window_rows,
    )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT symbol, model_repo_id, backend, points, windows
            FROM market_data.backtest_runs
            WHERE run_id = %s
            """,
            (run_id,),
        )
        stored_run = cur.fetchone()
        cur.execute(
            """
            SELECT window_index, target_start_utc, context_end_utc, last_input_close
            FROM market_data.backtest_windows
            WHERE run_id = %s
            ORDER BY window_index
            """,
            (run_id,),
        )
        stored_windows = cur.fetchall()
        cur.execute(
            """
            SELECT
                step_index,
                predicted_close,
                actual_close,
                normalized_deviation_pct,
                signed_deviation_pct,
                overshoot_label
            FROM market_data.backtest_prediction_steps
            WHERE run_id = %s
            ORDER BY window_id, step_index
            """,
            (run_id,),
        )
        stored_steps = cur.fetchall()

    assert stored_run == ("BTCUSDT", "stub/repo", "cpu", 10, 1)
    assert stored_windows == [
        (
            0,
            datetime(2024, 4, 1, 0, 4, tzinfo=timezone.utc),
            datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc),
            4.0,
        )
    ]
    assert stored_steps == [
        (0, 5.0, 5.0, 0.0, 0.0, "match"),
        (1, 6.0, 6.0, 0.0, 0.0, "match"),
    ]


def test_main_uses_loaded_frame_bounds_for_saved_run_coverage(monkeypatch) -> None:
    partial_day_frame = pd.DataFrame(
        {
            "open_time_utc": pd.date_range(
                "2024-04-01T12:00:00Z",
                periods=7,
                freq="1min",
                tz="UTC",
            ),
            "close": np.arange(100.0, 107.0, dtype=np.float64),
        }
    )
    args = argparse.Namespace(
        mode="backtest",
        day=date(2024, 4, 1),
        symbol="BTCUSDT",
        context_len=4,
        horizon_len=2,
        stride=1,
        batch_size=8,
        max_windows=None,
        freq=0,
        backend="cpu",
        repo_id="stub/repo",
        host="127.0.0.1",
        port=54329,
        db_name="timesfm_fin",
        user="timesfm",
        password="timesfm_dev",
        output_csv=None,
    )
    observed: dict[str, object] = {}

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def commit(self) -> None:
            observed["committed"] = True

    monkeypatch.setattr(crypto_minute_backtest, "parse_args", lambda: args)
    monkeypatch.setattr(
        crypto_minute_backtest,
        "postgres_settings_from_args",
        lambda parsed_args: parsed_args,
    )
    monkeypatch.setattr(
        crypto_minute_backtest,
        "build_model",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        crypto_minute_backtest,
        "connect_postgres",
        lambda **kwargs: FakeConnection(),
    )
    monkeypatch.setattr(
        crypto_minute_backtest,
        "load_backtest_frame",
        lambda **kwargs: partial_day_frame,
    )
    monkeypatch.setattr(
        crypto_minute_backtest,
        "run_backtest",
        lambda **kwargs: ({"points": 7, "windows": 1}, []),
    )

    def fake_save_backtest(**kwargs) -> int:
        observed["start_dt"] = kwargs["start_dt"]
        observed["end_dt"] = kwargs["end_dt"]
        return 42

    monkeypatch.setattr(crypto_minute_backtest, "save_backtest", fake_save_backtest)
    monkeypatch.setattr(crypto_minute_backtest, "print_summary", lambda **kwargs: None)

    crypto_minute_backtest.main()

    assert observed["start_dt"] == datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc)
    assert observed["end_dt"] == datetime(2024, 4, 1, 12, 6, tzinfo=timezone.utc)
    assert observed["committed"] is True


def test_print_summary_uses_human_readable_metric_labels(capsys) -> None:
    args = argparse.Namespace(
        day=date(2024, 4, 1),
        symbol="BTCUSDT",
        host="127.0.0.1",
        port=54329,
        db_name="timesfm_fin",
    )
    metrics = {
        "windows": 1,
        "mae": 33.574140625001746,
        "rmse": 38.27004199860898,
        "mape_pct": 0.047196569994895646,
        "smape_pct": 0.0471868454945735,
        "step1_directional_accuracy": 1.0,
        "end_directional_accuracy": 0.0,
        "hit_rate": 0.0,
        "strategy_mean_return": 0.00123456,
        "strategy_std": 0.00234567,
        "annual_return": 0.123456,
        "annualized_volatility": 0.234567,
        "sharpe_ratio": 0.526315,
    }

    crypto_minute_backtest.print_summary(
        args=args,
        start_dt=datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        end_dt=datetime(2024, 4, 1, 23, 59, tzinfo=timezone.utc),
        candle_count=1440,
        metrics=metrics,
        run_id=7,
    )

    output = capsys.readouterr().out

    assert "Forecast windows evaluated: 1 (one forecast block)" in output
    assert "Average absolute price error: 33.574141" in output
    assert "Root mean squared price error: 38.270042" in output
    assert "Average percentage error: 0.047197%" in output
    assert "Symmetric average percentage error: 0.047187%" in output
    assert "First predicted minute got the direction right: 100.00%" in output
    assert "Final predicted minute got the direction right: 0.00%" in output
    assert "Forecast windows with the correct overall direction: 0.00%" in output
    assert "Average simulated return per forecast window: 0.1235%" in output
    assert "Variation in simulated returns: 0.2346%" in output
    assert "Estimated annual return: 12.35%" in output
    assert "Estimated annualized volatility: 23.46%" in output
    assert "Return-to-volatility ratio: 0.526315" in output
    assert "MAE:" not in output
    assert "RMSE:" not in output
    assert "MAPE (%):" not in output
    assert "SMAPE (%):" not in output
