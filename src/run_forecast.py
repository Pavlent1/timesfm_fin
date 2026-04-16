import argparse
import os
from pathlib import Path


DEFAULT_REPO_ID = "pfnet/timesfm-1.0-200m-fin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run TimesFM_fin on a Yahoo Finance ticker or a local CSV file."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--ticker",
        help="Yahoo Finance ticker symbol, for example AAPL or MSFT.",
    )
    source.add_argument(
        "--csv",
        type=Path,
        help="Path to a CSV file containing a price series.",
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
        default="3y",
        help="Yahoo Finance lookback period when using --ticker.",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        help="Yahoo Finance interval when using --ticker.",
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
        default=32,
        help="Number of future steps to predict.",
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
        "--checkpoint-path",
        default=None,
        help="Optional local TimesFM checkpoint path. Overrides --repo-id when provided.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional path to save the forecast as CSV.",
    )
    return parser.parse_args()


def load_series_from_yahoo(ticker: str, column: str, period: str, interval: str):
    import pandas as pd
    import yfinance as yf

    data = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )
    if data.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'.")

    if isinstance(data.columns, pd.MultiIndex):
        if column not in data.columns.get_level_values(0):
            raise ValueError(f"Column '{column}' not found in Yahoo Finance response.")
        series = data[column].iloc[:, 0]
    else:
        if column not in data.columns:
            raise ValueError(f"Column '{column}' not found in Yahoo Finance response.")
        series = data[column]

    series = series.dropna().astype(float)
    if series.empty:
        raise ValueError(f"Column '{column}' has no numeric values for ticker '{ticker}'.")
    series.name = column
    return series


def load_series_from_csv(path: Path, column: str, date_column: str | None):
    import pandas as pd

    df = pd.read_csv(path)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in {path}.")

    if date_column is not None:
        if date_column not in df.columns:
            raise ValueError(f"Date column '{date_column}' not found in {path}.")
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df = df.dropna(subset=[date_column])
        df = df.sort_values(date_column)
        series = df.set_index(date_column)[column]
    else:
        series = df[column]

    series = series.dropna().astype(float)
    if series.empty:
        raise ValueError(f"Column '{column}' has no numeric values in {path}.")
    series.name = column
    return series


def infer_future_index(series, horizon_len: int):
    import pandas as pd

    if not isinstance(series.index, pd.DatetimeIndex):
        return None

    if len(series.index) < 3:
        return None

    inferred = pd.infer_freq(series.index)
    if inferred is None:
        return None

    start = series.index[-1]
    return pd.date_range(start=start, periods=horizon_len + 1, freq=inferred)[1:]


def build_model(
    context_len: int,
    horizon_len: int,
    backend: str,
    repo_id: str,
    checkpoint_path: str | None = None,
):
    if backend == "cpu":
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
    if checkpoint_path:
        checkpoint = timesfm.TimesFmCheckpoint(
            version="jax",
            path=checkpoint_path,
        )
    else:
        checkpoint = timesfm.TimesFmCheckpoint(
            version="jax",
            huggingface_repo_id=repo_id,
        )
    return timesfm.TimesFm(hparams=hparams, checkpoint=checkpoint)


def main() -> None:
    import numpy as np
    import pandas as pd

    args = parse_args()

    if args.ticker:
        series = load_series_from_yahoo(
            ticker=args.ticker,
            column=args.column,
            period=args.period,
            interval=args.interval,
        )
        source_label = args.ticker
    else:
        series = load_series_from_csv(
            path=args.csv,
            column=args.column,
            date_column=args.date_column,
        )
        source_label = str(args.csv)

    context = series.tail(args.context_len).to_numpy(dtype=np.float32)
    if context.size < 32:
        raise ValueError(
            f"Need at least 32 observations to run TimesFM reliably, got {context.size}."
        )

    model = build_model(
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        backend=args.backend,
        repo_id=args.repo_id,
        checkpoint_path=getattr(args, "checkpoint_path", None),
    )

    point_forecast, _ = model.forecast([context], freq=[args.freq])
    forecast = np.asarray(point_forecast[0], dtype=float)

    future_index = infer_future_index(series, args.horizon_len)
    forecast_df = pd.DataFrame(
        {
            "step": list(range(1, args.horizon_len + 1)),
            "forecast": forecast,
        }
    )
    if future_index is not None:
        forecast_df.insert(0, "ds", future_index)

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        forecast_df.to_csv(args.output_csv, index=False)

    print(f"Source: {source_label}")
    print(f"Checkpoint: {getattr(args, 'checkpoint_path', None) or args.repo_id}")
    print(f"Context points used: {context.size}")
    print(f"Latest observed {args.column}: {float(series.iloc[-1]):.4f}")
    print("")
    print(forecast_df.to_string(index=False))

    if args.output_csv is not None:
        print("")
        print(f"Saved forecast to: {args.output_csv}")


if __name__ == "__main__":
    main()
