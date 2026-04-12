import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from run_forecast import (
    DEFAULT_REPO_ID,
    build_model,
    load_series_from_csv,
    load_series_from_yahoo,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rolling backtest for TimesFM_fin on tickers or a local CSV."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--tickers",
        nargs="+",
        help="One or more Yahoo Finance tickers, for example AAPL MSFT NVDA.",
    )
    source.add_argument(
        "--csv",
        type=Path,
        help="Path to a CSV file containing a single price series.",
    )

    parser.add_argument(
        "--column",
        default="Close",
        help="Value column to forecast when reading CSV or Yahoo Finance data.",
    )
    parser.add_argument(
        "--date-column",
        default=None,
        help="Optional date column in the CSV file. If omitted, row order is preserved.",
    )
    parser.add_argument(
        "--period",
        default="5y",
        help="Yahoo Finance lookback period when using --tickers.",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval when using --tickers.",
    )
    parser.add_argument(
        "--context-len",
        type=int,
        default=512,
        help="Maximum context length passed to the model.",
    )
    parser.add_argument(
        "--horizon-len",
        type=int,
        default=16,
        help="Number of future steps to predict per evaluation window.",
    )
    parser.add_argument(
        "--test-points",
        type=int,
        default=128,
        help="How many of the latest points to backtest across.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Window stride. Use larger values to evaluate faster.",
    )
    parser.add_argument(
        "--freq",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="TimesFM frequency bucket: 0=daily-or-faster, 1=weekly/monthly, 2=quarterly/yearly.",
    )
    parser.add_argument(
        "--backend",
        default="cpu",
        choices=["cpu", "gpu", "tpu"],
        help="Backend used by TimesFM.",
    )
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help="Hugging Face checkpoint repo id.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional path to save the summary table as CSV.",
    )
    return parser.parse_args()


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.abs(y_true) + np.abs(y_pred)
    denom = np.where(denom == 0.0, 1.0, denom)
    return float(np.mean(200.0 * np.abs(y_pred - y_true) / denom))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(np.abs(y_true) < 1e-8, np.nan, np.abs(y_true))
    return float(np.nanmean(100.0 * np.abs(y_pred - y_true) / denom))


def directional_accuracy(
    predicted: np.ndarray,
    actual: np.ndarray,
    baseline: np.ndarray,
) -> float:
    pred_dir = np.sign(predicted - baseline)
    actual_dir = np.sign(actual - baseline)
    return float(np.mean(pred_dir == actual_dir))


def evaluate_series(
    model,
    label: str,
    series: pd.Series,
    context_len: int,
    horizon_len: int,
    test_points: int,
    stride: int,
    freq: int,
) -> dict[str, float | int | str]:
    values = series.dropna().astype(float).to_numpy(dtype=np.float32)
    if values.size < context_len + horizon_len + 1:
        raise ValueError(
            f"{label}: need at least {context_len + horizon_len + 1} points, got {values.size}."
        )

    eval_start = max(context_len, values.size - test_points - horizon_len + 1)
    last_start = values.size - horizon_len
    if eval_start > last_start:
        raise ValueError(
            f"{label}: not enough points for the requested test span and horizon."
        )

    all_predictions = []
    all_actuals = []
    all_last_context = []

    for start in range(eval_start, last_start + 1, stride):
        context = values[start - context_len:start]
        actual = values[start:start + horizon_len]
        prediction, _ = model.forecast([context], freq=[freq])
        prediction = np.asarray(prediction[0], dtype=np.float64)[:horizon_len]

        all_predictions.append(prediction)
        all_actuals.append(actual.astype(np.float64))
        all_last_context.append(float(context[-1]))

    predictions = np.vstack(all_predictions)
    actuals = np.vstack(all_actuals)
    last_context = np.asarray(all_last_context, dtype=np.float64)

    flat_predictions = predictions.reshape(-1)
    flat_actuals = actuals.reshape(-1)

    step1_predictions = predictions[:, 0]
    step1_actuals = actuals[:, 0]
    end_predictions = predictions[:, -1]
    end_actuals = actuals[:, -1]

    return {
        "series": label,
        "points": int(values.size),
        "windows": int(predictions.shape[0]),
        "horizon_len": int(horizon_len),
        "mae": float(np.mean(np.abs(flat_predictions - flat_actuals))),
        "rmse": float(np.sqrt(np.mean((flat_predictions - flat_actuals) ** 2))),
        "mape_pct": mape(flat_actuals, flat_predictions),
        "smape_pct": smape(flat_actuals, flat_predictions),
        "step1_mae": float(np.mean(np.abs(step1_predictions - step1_actuals))),
        "step1_rmse": float(np.sqrt(np.mean((step1_predictions - step1_actuals) ** 2))),
        "step1_directional_accuracy": directional_accuracy(
            step1_predictions, step1_actuals, last_context
        ),
        "end_directional_accuracy": directional_accuracy(
            end_predictions, end_actuals, last_context
        ),
    }


def format_results(results: list[dict[str, float | int | str]]) -> pd.DataFrame:
    frame = pd.DataFrame(results)
    numeric_columns = [
        "mae",
        "rmse",
        "mape_pct",
        "smape_pct",
        "step1_mae",
        "step1_rmse",
        "step1_directional_accuracy",
        "end_directional_accuracy",
    ]
    frame[numeric_columns] = frame[numeric_columns].applymap(
        lambda value: round(float(value), 6)
    )
    return frame.sort_values("series").reset_index(drop=True)


def main() -> None:
    args = parse_args()

    model = build_model(
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        backend=args.backend,
        repo_id=args.repo_id,
    )

    results = []
    if args.tickers:
        for ticker in args.tickers:
            series = load_series_from_yahoo(
                ticker=ticker,
                column=args.column,
                period=args.period,
                interval=args.interval,
            )
            results.append(
                evaluate_series(
                    model=model,
                    label=ticker,
                    series=series,
                    context_len=args.context_len,
                    horizon_len=args.horizon_len,
                    test_points=args.test_points,
                    stride=args.stride,
                    freq=args.freq,
                )
            )
    else:
        series = load_series_from_csv(
            path=args.csv,
            column=args.column,
            date_column=args.date_column,
        )
        results.append(
            evaluate_series(
                model=model,
                label=str(args.csv),
                series=series,
                context_len=args.context_len,
                horizon_len=args.horizon_len,
                test_points=args.test_points,
                stride=args.stride,
                freq=args.freq,
            )
        )

    results_df = format_results(results)
    print(results_df.to_string(index=False))

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(args.output_csv, index=False)
        print("")
        print(f"Saved summary to: {args.output_csv}")


if __name__ == "__main__":
    main()
