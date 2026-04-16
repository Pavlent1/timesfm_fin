from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


ForecastFn = Callable[..., np.ndarray]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a trained checkpoint against the explicit Phase 3 holdout series "
            "and write evaluation_summary.json."
        )
    )
    parser.add_argument("--holdout-series", type=Path, required=True, help="Explicit holdout_series.csv path.")
    parser.add_argument("--output", type=Path, required=True, help="Summary JSON output path.")
    parser.add_argument("--checkpoint-reference", required=True, help="Checkpoint path or repo id.")
    parser.add_argument(
        "--checkpoint-kind",
        choices=["path", "repo"],
        required=True,
        help="Whether --checkpoint-reference is a local path or Hugging Face repo id.",
    )
    parser.add_argument("--context-len", type=int, default=512, help="Evaluation context length.")
    parser.add_argument("--horizon-len", type=int, default=128, help="Evaluation horizon length.")
    parser.add_argument("--stride", type=int, default=128, help="Step size between holdout windows.")
    parser.add_argument(
        "--backend",
        default="cpu",
        choices=["cpu", "gpu", "tpu"],
        help="Backend used to load the TimesFM checkpoint.",
    )
    return parser.parse_args(argv)


def load_holdout_series(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required_columns = {"symbol", "observation_time_utc", "close_price"}
    missing = required_columns - set(frame.columns)
    if missing:
        raise ValueError(
            "Holdout artifact is missing required columns: " + ", ".join(sorted(missing))
        )
    frame = frame.copy()
    frame["observation_time_utc"] = pd.to_datetime(frame["observation_time_utc"], utc=True)
    frame["close_price"] = frame["close_price"].astype(float)
    return frame.sort_values(["symbol", "observation_time_utc"]).reset_index(drop=True)


def default_forecast_contexts(
    *,
    checkpoint_reference: str,
    checkpoint_kind: str,
    contexts: list[np.ndarray],
    context_len: int,
    horizon_len: int,
    backend: str = "cpu",
    freq: int = 0,
) -> np.ndarray:
    if backend == "cpu":
        import os

        os.environ.setdefault("JAX_PLATFORMS", "cpu")

    import timesfm

    hparams = timesfm.TimesFmHparams(
        context_len=context_len,
        horizon_len=horizon_len,
        input_patch_len=32,
        output_patch_len=128,
        num_layers=20,
        model_dims=1280,
        backend=backend,
    )
    if checkpoint_kind == "path":
        checkpoint = timesfm.TimesFmCheckpoint(
            version="jax",
            path=checkpoint_reference,
        )
    else:
        checkpoint = timesfm.TimesFmCheckpoint(
            version="jax",
            huggingface_repo_id=checkpoint_reference,
        )
    model = timesfm.TimesFm(hparams=hparams, checkpoint=checkpoint)
    forecast, _ = model.forecast(contexts, freq=[freq] * len(contexts))
    return np.asarray(forecast, dtype=np.float64)[:, :horizon_len]


def build_symbol_windows(
    frame: pd.DataFrame,
    *,
    context_len: int,
    horizon_len: int,
    stride: int,
) -> list[dict[str, object]]:
    values = frame["close_price"].to_numpy(dtype=np.float64)
    timestamps = pd.to_datetime(frame["observation_time_utc"], utc=True)
    if len(values) < context_len + horizon_len:
        raise ValueError(
            f"{frame['symbol'].iloc[0]} does not have enough holdout points for the requested context/horizon."
        )

    windows: list[dict[str, object]] = []
    for start_index in range(context_len, len(values) - horizon_len + 1, stride):
        windows.append(
            {
                "context": values[start_index - context_len : start_index].astype(np.float32),
                "actual": values[start_index : start_index + horizon_len].astype(np.float64),
                "target_start_utc": timestamps.iloc[start_index],
                "target_end_utc": timestamps.iloc[start_index + horizon_len - 1],
            }
        )
    if not windows:
        raise ValueError(
            f"{frame['symbol'].iloc[0]} produced zero holdout windows for the requested stride."
        )
    return windows


def summarize_error_metrics(errors: np.ndarray, actuals: np.ndarray) -> dict[str, float]:
    absolute = np.abs(errors)
    safe_actuals = np.where(actuals == 0.0, np.nan, actuals)
    mape = np.nanmean(np.abs(errors / safe_actuals)) * 100.0
    if np.isnan(mape):
        mape = 0.0
    return {
        "mae": float(np.mean(absolute)),
        "rmse": float(np.sqrt(np.mean(np.square(errors)))),
        "mape_pct": float(mape),
    }


def evaluate_training_run(
    *,
    holdout_series_path: Path,
    output_path: Path,
    checkpoint_reference: str,
    checkpoint_kind: str,
    context_len: int = 512,
    horizon_len: int = 128,
    stride: int = 128,
    backend: str = "cpu",
    forecast_contexts: ForecastFn | None = None,
) -> dict[str, object]:
    frame = load_holdout_series(holdout_series_path)
    forecast_fn = forecast_contexts or default_forecast_contexts

    symbol_summaries: list[dict[str, object]] = []
    overall_predictions: list[float] = []
    overall_actuals: list[float] = []
    total_windows = 0

    for symbol, symbol_frame in frame.groupby("symbol", sort=True):
        windows = build_symbol_windows(
            symbol_frame,
            context_len=context_len,
            horizon_len=horizon_len,
            stride=stride,
        )
        predictions = forecast_fn(
            checkpoint_reference=checkpoint_reference,
            checkpoint_kind=checkpoint_kind,
            contexts=[window["context"] for window in windows],
            context_len=context_len,
            horizon_len=horizon_len,
            backend=backend,
        )
        actuals = np.asarray([window["actual"] for window in windows], dtype=np.float64)
        errors = predictions - actuals
        metrics = summarize_error_metrics(errors, actuals)
        total_windows += len(windows)
        overall_predictions.extend(predictions.reshape(-1).tolist())
        overall_actuals.extend(actuals.reshape(-1).tolist())
        symbol_summaries.append(
            {
                "symbol": symbol,
                "window_count": len(windows),
                "point_count": int(actuals.size),
                "holdout_start_utc": symbol_frame["observation_time_utc"].iloc[0].isoformat(),
                "holdout_end_utc": symbol_frame["observation_time_utc"].iloc[-1].isoformat(),
                "metrics": metrics,
            }
        )

    overall_predictions_array = np.asarray(overall_predictions, dtype=np.float64)
    overall_actuals_array = np.asarray(overall_actuals, dtype=np.float64)
    overall_errors = overall_predictions_array - overall_actuals_array
    summary = {
        "checkpoint_reference": checkpoint_reference,
        "checkpoint_kind": checkpoint_kind,
        "holdout_series_path": str(holdout_series_path),
        "canonical_for_phase3_comparison": True,
        "trainer_internal_eval_is_canonical": False,
        "context_len": context_len,
        "horizon_len": horizon_len,
        "stride": stride,
        "window_count": total_windows,
        "point_count": int(overall_actuals_array.size),
        "overall_metrics": summarize_error_metrics(overall_errors, overall_actuals_array),
        "symbol_summaries": symbol_summaries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = evaluate_training_run(
        holdout_series_path=args.holdout_series,
        output_path=args.output,
        checkpoint_reference=args.checkpoint_reference,
        checkpoint_kind=args.checkpoint_kind,
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        stride=args.stride,
        backend=args.backend,
    )
    print(f"Saved evaluation summary to: {args.output}")
    print(f"Windows evaluated: {summary['window_count']}")


if __name__ == "__main__":
    main()
