from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

import crypto_prediction_backtest

from crypto_prediction_algo_export.btc_microstructure_model import (
    BtcMicrostructure,
    IndicatorSignals,
    SignalEvaluation,
)


def build_candles(count: int = 80) -> list[crypto_prediction_backtest.Candle]:
    candles: list[crypto_prediction_backtest.Candle] = []
    for index in range(count):
        price = 100.0 + index
        candles.append(
            crypto_prediction_backtest.Candle(
                timestamp=datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
                + timedelta(minutes=index),
                open=price - 0.5,
                high=price + 0.5,
                low=price - 1.0,
                close=price,
                volume=10.0 + index,
            )
        )
    return candles


def fake_evaluator(**kwargs) -> SignalEvaluation:
    market = kwargs["market"]
    assert market.up_price == 0.5
    return SignalEvaluation(
        valid=True,
        actionable=True,
        direction="up",
        model_up_probability=0.6,
        market_up_probability=0.5,
        signed_up_edge=0.1,
        raw_edge=0.1,
        tradable_edge=0.1,
        entry_price=0.5,
        confidence=0.4,
        kelly_fraction=0.01,
        suggested_size=10.0,
        passes_filters=True,
        passes_threshold=True,
        time_remaining_seconds=300.0,
        filter_reasons=(),
        microstructure=BtcMicrostructure(
            rsi=55.0,
            momentum_1m=0.06,
            momentum_5m=0.10,
            momentum_15m=0.14,
            vwap=100.0,
            vwap_deviation=0.08,
            sma_crossover=0.04,
            volatility=0.12,
            price=100.0,
        ),
        indicators=IndicatorSignals(
            rsi_signal=0.0,
            momentum_signal=0.6,
            vwap_signal=0.5,
            sma_signal=0.3,
            skew_signal=0.0,
            composite=0.2,
            up_votes=3,
            down_votes=0,
        ),
        reasoning="ok",
    )


def test_run_backtest_returns_timesfm_style_step_metrics() -> None:
    metrics, step_stats_rows, detail_rows = crypto_prediction_backtest.run_backtest(
        symbol="BTCUSDT",
        candles=build_candles(),
        history_len=60,
        future_candles=5,
        stride=5,
        up_price=0.5,
        down_price=0.5,
        window_minutes=5,
        max_windows=2,
        evaluator=fake_evaluator,
    )

    assert metrics == {
        "points": 80,
        "requested_windows": 2,
        "valid_windows": 2,
        "invalid_windows": 0,
        "history_len": 60,
        "future_candles": 5,
    }
    assert len(step_stats_rows) == 5
    assert len(detail_rows) == 10

    first_step = step_stats_rows[0]
    first_step_detail_rows = [row for row in detail_rows if row["step_index"] == 0]

    assert first_step["step_index"] == 0
    assert first_step["step_count"] == 2
    assert first_step["avg_normalized_deviation_pct"] == pytest.approx(
        sum(float(row["normalized_deviation_pct"]) for row in first_step_detail_rows) / 2.0
    )
    assert first_step["stddev_normalized_deviation_pct"] >= 0.0
    assert first_step["avg_overshoot_deviation_pct"] == 0.0
    assert first_step["avg_undershoot_deviation_pct"] == pytest.approx(
        first_step["avg_normalized_deviation_pct"]
    )
    assert first_step["match_count"] == 0
    assert first_step["avg_signed_deviation_pct"] < 0.0
    assert first_step["direction_guess_accuracy_pct"] == 100.0

    first_detail = detail_rows[0]
    assert first_detail["step_index"] == 0
    assert first_detail["predicted_close"] == pytest.approx(159.100488)
    assert first_detail["actual_close"] == 160.0
    assert first_detail["overshoot_label"] == "undershoot"
    assert first_detail["direction_guess_correct"] == 1


def test_run_backtest_counts_invalid_windows_and_raises_if_none_valid() -> None:
    def invalid_evaluator(**kwargs) -> SignalEvaluation:
        return SignalEvaluation(
            valid=False,
            actionable=False,
            direction="up",
            model_up_probability=0.5,
            market_up_probability=0.5,
            signed_up_edge=0.0,
            raw_edge=0.0,
            tradable_edge=0.0,
            entry_price=0.5,
            confidence=0.0,
            kelly_fraction=0.0,
            suggested_size=0.0,
            passes_filters=False,
            passes_threshold=False,
            time_remaining_seconds=None,
            filter_reasons=("invalid",),
            reasoning="invalid",
        )

    with pytest.raises(ValueError, match="zero valid evaluation windows"):
        crypto_prediction_backtest.run_backtest(
            symbol="BTCUSDT",
            candles=build_candles(),
            history_len=60,
            future_candles=5,
            stride=5,
            up_price=0.5,
            down_price=0.5,
            window_minutes=5,
            evaluator=invalid_evaluator,
        )


def test_render_report_includes_directional_stats_note() -> None:
    args = argparse.Namespace(
        symbol="BTCUSDT",
        day=date(2024, 4, 1),
        days=2,
        stride=3,
        up_price=0.5,
        down_price=0.5,
        future_candles=5,
    )

    report = crypto_prediction_backtest.render_report(
        args=args,
        requested_start_dt=datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        requested_end_dt=datetime(2024, 4, 3, 0, 0, tzinfo=timezone.utc),
        loaded_candle_count=2940,
        evaluation_candle_count=2880,
        lookback_candle_count=60,
        window_minutes=5,
        metrics={
            "history_len": 60,
            "future_candles": 5,
            "requested_windows": 960,
            "valid_windows": 950,
            "invalid_windows": 10,
            "points": 2940,
        },
        step_stats_rows=[
            {
                "step_index": 0,
                "step_count": 950,
                "avg_normalized_deviation_pct": 0.23,
                "stddev_normalized_deviation_pct": 0.11,
                "avg_overshoot_deviation_pct": 0.28,
                "avg_undershoot_deviation_pct": 0.17,
                "match_count": 0,
                "avg_signed_deviation_pct": 0.04,
                "direction_guess_accuracy_pct": 63.5,
            }
        ],
    )

    assert "Crypto Prediction Strategy Backtest Report" in report
    assert "Forecast windows: 950" in report
    assert "Per-step stats" in report
    assert "avg_normalized_deviation_pct" in report
    assert "avg_overshoot_deviation_pct" in report
    assert "avg_undershoot_deviation_pct" in report
    assert "direction_guess_accuracy_pct" in report
    assert "same deviation metrics as the TimesFM backtest" in report


def test_default_report_path_uses_symbol_range_and_horizon() -> None:
    args = argparse.Namespace(
        symbol="BTCUSDT",
        day=date(2024, 4, 1),
        days=3,
        future_candles=5,
    )

    assert crypto_prediction_backtest.default_report_path(args) == Path(
        "outputs/backtests/crypto_prediction_backtest_btcusdt_2024-04-01_to_2024-04-03_next5.txt"
    )


def test_write_detail_csv_writes_expected_columns(tmp_path: Path) -> None:
    output_path = tmp_path / "detail.csv"
    crypto_prediction_backtest.write_detail_csv(
        output_path,
        [
            {
                "decision_time_utc": "2024-04-01T00:59:00+00:00",
                "target_time_utc": "2024-04-01T01:00:00+00:00",
                "step_index": 0,
                "last_input_close": 159.0,
                "predicted_close": 159.08904,
                "actual_close": 160.0,
                "normalized_deviation_pct": 0.56935,
                "signed_deviation_pct": -0.56935,
                "overshoot_label": "undershoot",
                "direction_guess_correct": 1,
                "actionable": True,
                "passes_filters": True,
                "passes_threshold": True,
                "model_up_probability_pct": 60.0,
                "market_up_probability_pct": 50.0,
                "raw_edge_pct": 10.0,
                "confidence_pct": 40.0,
                "composite_signal": 0.2,
                "projected_return_pct": 0.056,
            }
        ],
    )

    text = output_path.read_text(encoding="utf-8")
    assert "decision_time_utc" in text
    assert "normalized_deviation_pct" in text
    assert "direction_guess_correct" in text
    assert "2024-04-01T01:00:00+00:00" in text
