from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import run_forecast


class StubForecastModel:
    def __init__(self, forecast_values: list[float]):
        self.forecast_values = np.asarray([forecast_values], dtype=np.float64)

    def forecast(self, contexts, freq):
        assert len(contexts) == 1
        return self.forecast_values, None


def test_load_series_from_csv_sorts_dates_and_drops_invalid_rows(tmp_path) -> None:
    csv_path = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {"Date": "2024-04-03", "Close": 103.0},
            {"Date": "not-a-date", "Close": 999.0},
            {"Date": "2024-04-01", "Close": 101.0},
            {"Date": "2024-04-02", "Close": 102.0},
        ]
    ).to_csv(csv_path, index=False)

    series = run_forecast.load_series_from_csv(
        csv_path,
        column="Close",
        date_column="Date",
    )

    assert series.tolist() == [101.0, 102.0, 103.0]
    assert list(series.index.strftime("%Y-%m-%d")) == [
        "2024-04-01",
        "2024-04-02",
        "2024-04-03",
    ]


def test_load_series_from_yahoo_handles_multiindex_columns(monkeypatch) -> None:
    frame = pd.DataFrame(
        {
            ("Close", "AAPL"): [100.0, 101.0],
            ("Open", "AAPL"): [99.0, 100.0],
        }
    )
    frame.columns = pd.MultiIndex.from_tuples(frame.columns)

    def fake_download(**kwargs):
        assert kwargs["tickers"] == "AAPL"
        return frame

    monkeypatch.setitem(
        sys.modules,
        "yfinance",
        types.SimpleNamespace(download=fake_download),
    )

    series = run_forecast.load_series_from_yahoo(
        ticker="AAPL",
        column="Close",
        period="1mo",
        interval="1d",
    )

    assert series.tolist() == [100.0, 101.0]
    assert series.name == "Close"


def test_infer_future_index_returns_regular_frequency_dates() -> None:
    series = pd.Series(
        [100.0, 101.0, 102.0, 103.0],
        index=pd.date_range("2024-04-01", periods=4, freq="1D", tz="UTC"),
    )

    future_index = run_forecast.infer_future_index(series, horizon_len=3)

    assert list(future_index.strftime("%Y-%m-%dT%H:%M:%SZ")) == [
        "2024-04-05T00:00:00Z",
        "2024-04-06T00:00:00Z",
        "2024-04-07T00:00:00Z",
    ]


def test_build_model_uses_stubbed_timesfm_and_sets_cpu_platform(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeTimesFm:
        def __init__(self, *, hparams, checkpoint):
            captured["hparams"] = hparams
            captured["checkpoint"] = checkpoint

    def fake_hparams(**kwargs):
        return {"kind": "hparams", **kwargs}

    def fake_checkpoint(**kwargs):
        return {"kind": "checkpoint", **kwargs}

    monkeypatch.delenv("JAX_PLATFORMS", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "timesfm",
        types.SimpleNamespace(
            TimesFm=FakeTimesFm,
            TimesFmHparams=fake_hparams,
            TimesFmCheckpoint=fake_checkpoint,
        ),
    )

    model = run_forecast.build_model(
        context_len=64,
        horizon_len=8,
        backend="cpu",
        repo_id="custom/repo",
    )

    assert isinstance(model, FakeTimesFm)
    assert captured["hparams"]["context_len"] == 64
    assert captured["hparams"]["horizon_len"] == 8
    assert captured["hparams"]["backend"] == "cpu"
    assert captured["checkpoint"] == {
        "kind": "checkpoint",
        "version": "jax",
        "huggingface_repo_id": "custom/repo",
    }
    assert run_forecast.os.environ["JAX_PLATFORMS"] == "cpu"


def test_main_forecasts_from_csv_and_writes_output(monkeypatch, tmp_path, capsys) -> None:
    csv_path = tmp_path / "series.csv"
    output_csv = tmp_path / "forecast.csv"
    pd.DataFrame(
        {
            "Date": pd.date_range("2024-04-01", periods=40, freq="1D", tz="UTC"),
            "Close": np.arange(100.0, 140.0, dtype=np.float64),
        }
    ).to_csv(csv_path, index=False)

    args = argparse.Namespace(
        ticker=None,
        csv=csv_path,
        column="Close",
        date_column="Date",
        period="3y",
        interval="1d",
        context_len=32,
        horizon_len=3,
        freq=0,
        backend="cpu",
        repo_id="stub/repo",
        output_csv=output_csv,
    )

    monkeypatch.setattr(run_forecast, "parse_args", lambda: args)
    monkeypatch.setattr(
        run_forecast,
        "build_model",
        lambda **kwargs: StubForecastModel([141.0, 142.0, 143.0]),
    )

    run_forecast.main()

    written = pd.read_csv(output_csv)
    assert list(written.columns) == ["ds", "step", "forecast"]
    assert written["forecast"].tolist() == [141.0, 142.0, 143.0]
    output = capsys.readouterr().out
    assert f"Source: {csv_path}" in output
    assert "Checkpoint: stub/repo" in output
    assert "Saved forecast to:" in output
