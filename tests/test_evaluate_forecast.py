from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import evaluate_forecast


class PerfectForecastModel:
    def forecast(self, contexts, freq):
        forecasts = []
        for context in contexts:
            last_value = float(context[-1])
            forecasts.append([last_value + 1.0, last_value + 2.0])
        return np.asarray(forecasts, dtype=np.float64), None


def test_metric_helpers_handle_zero_denominators_and_direction() -> None:
    y_true = np.asarray([0.0, 100.0], dtype=np.float64)
    y_pred = np.asarray([0.0, 110.0], dtype=np.float64)
    baseline = np.asarray([10.0, 10.0], dtype=np.float64)
    predicted = np.asarray([11.0, 9.0], dtype=np.float64)
    actual = np.asarray([12.0, 8.0], dtype=np.float64)

    assert evaluate_forecast.mape(y_true, y_pred) == pytest.approx(10.0)
    assert evaluate_forecast.smape(y_true, y_pred) == pytest.approx(4.7619047619)
    assert evaluate_forecast.directional_accuracy(predicted, actual, baseline) == 1.0


def test_evaluate_series_rejects_short_input() -> None:
    series = pd.Series([1.0, 2.0, 3.0, 4.0])

    with pytest.raises(ValueError, match="need at least 7 points"):
        evaluate_forecast.evaluate_series(
            model=PerfectForecastModel(),
            label="BTC",
            series=series,
            context_len=4,
            horizon_len=2,
            test_points=4,
            stride=1,
            freq=0,
        )


def test_evaluate_series_aggregates_perfect_predictions() -> None:
    series = pd.Series(np.arange(1.0, 13.0, dtype=np.float64))

    result = evaluate_forecast.evaluate_series(
        model=PerfectForecastModel(),
        label="BTC",
        series=series,
        context_len=4,
        horizon_len=2,
        test_points=4,
        stride=2,
        freq=0,
    )

    assert result["series"] == "BTC"
    assert result["points"] == 12
    assert result["windows"] == 2
    assert result["mae"] == 0.0
    assert result["rmse"] == 0.0
    assert result["mape_pct"] == 0.0
    assert result["smape_pct"] == 0.0
    assert result["step1_mae"] == 0.0
    assert result["step1_rmse"] == 0.0
    assert result["step1_directional_accuracy"] == 1.0
    assert result["end_directional_accuracy"] == 1.0


def test_format_results_sorts_rows_and_rounds_numeric_fields() -> None:
    frame = evaluate_forecast.format_results(
        [
            {
                "series": "SOL",
                "points": 5,
                "windows": 1,
                "horizon_len": 2,
                "mae": 1.123456789,
                "rmse": 2.123456789,
                "mape_pct": 3.123456789,
                "smape_pct": 4.123456789,
                "step1_mae": 5.123456789,
                "step1_rmse": 6.123456789,
                "step1_directional_accuracy": 0.666666666,
                "end_directional_accuracy": 0.333333333,
            },
            {
                "series": "BTC",
                "points": 5,
                "windows": 1,
                "horizon_len": 2,
                "mae": 0.1,
                "rmse": 0.2,
                "mape_pct": 0.3,
                "smape_pct": 0.4,
                "step1_mae": 0.5,
                "step1_rmse": 0.6,
                "step1_directional_accuracy": 1.0,
                "end_directional_accuracy": 0.0,
            },
        ]
    )

    assert frame["series"].tolist() == ["BTC", "SOL"]
    assert frame.loc[1, "mae"] == pytest.approx(1.123457)
    assert frame.loc[1, "step1_directional_accuracy"] == pytest.approx(0.666667)
