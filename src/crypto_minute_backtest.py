import argparse
import json
import math
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from evaluate_forecast import directional_accuracy, mape, smape
from run_forecast import DEFAULT_REPO_ID, build_model


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
ONE_MINUTE_MS = 60_000
MINUTES_PER_YEAR = 365 * 24 * 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Binance 1-minute BTC candles into SQLite and run either "
            "a rolling TimesFM backtest or a single live forecast."
        )
    )
    parser.add_argument(
        "--mode",
        default="backtest",
        choices=["backtest", "live"],
        help="Run a historical backtest or a single live forecast.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("outputs/crypto_backtest.sqlite"),
        help="SQLite database used for candles, per-window predictions, and summaries.",
    )
    parser.add_argument(
        "--symbol",
        default="BTCUSDT",
        help="Binance spot symbol to fetch. Default: BTCUSDT.",
    )
    parser.add_argument(
        "--day",
        type=parse_utc_day,
        default=default_previous_utc_day(),
        help=(
            "UTC day to backtest in YYYY-MM-DD format. "
            "Default: the previous UTC day."
        ),
    )
    parser.add_argument(
        "--context-len",
        type=int,
        default=512,
        help="Maximum context length passed to TimesFM.",
    )
    parser.add_argument(
        "--horizon-len",
        type=int,
        default=16,
        help="Number of future 1-minute candles predicted per window.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Step size between forecast origins.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="How many rolling windows to forecast in one TimesFM call.",
    )
    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="Optional cap on rolling windows, useful for quick smoke tests.",
    )
    parser.add_argument(
        "--freq",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="TimesFM frequency bucket. Use 0 for minute data.",
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
        help="Optional CSV output path for live forecasts.",
    )
    return parser.parse_args()


def parse_utc_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_previous_utc_day() -> date:
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()


def day_bounds_utc(target_day: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(target_day, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt


def latest_closed_minute_bounds(context_len: int) -> tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    end_dt = now_utc
    start_dt = end_dt - timedelta(minutes=context_len)
    return start_dt, end_dt


def to_utc_iso(timestamp_ms: int) -> str:
    return (
        datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candles (
            exchange TEXT NOT NULL,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            open_time_ms INTEGER NOT NULL,
            open_time_utc TEXT NOT NULL,
            close_time_ms INTEGER NOT NULL,
            close_time_utc TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            quote_asset_volume REAL NOT NULL,
            trades INTEGER NOT NULL,
            taker_buy_base_volume REAL NOT NULL,
            taker_buy_quote_volume REAL NOT NULL,
            PRIMARY KEY (exchange, symbol, interval, open_time_ms)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS backtest_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at_utc TEXT NOT NULL,
            exchange TEXT NOT NULL,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            model_repo_id TEXT NOT NULL,
            backend TEXT NOT NULL,
            freq_bucket INTEGER NOT NULL,
            context_len INTEGER NOT NULL,
            horizon_len INTEGER NOT NULL,
            stride INTEGER NOT NULL,
            batch_size INTEGER NOT NULL,
            data_start_utc TEXT NOT NULL,
            data_end_utc TEXT NOT NULL,
            points INTEGER NOT NULL,
            windows INTEGER NOT NULL,
            mae REAL NOT NULL,
            rmse REAL NOT NULL,
            mape_pct REAL NOT NULL,
            smape_pct REAL NOT NULL,
            step1_mae REAL NOT NULL,
            step1_rmse REAL NOT NULL,
            step1_directional_accuracy REAL NOT NULL,
            end_directional_accuracy REAL NOT NULL,
            hit_rate REAL NOT NULL,
            strategy_mean_return REAL NOT NULL,
            strategy_std REAL NOT NULL,
            annual_return REAL NOT NULL,
            annualized_volatility REAL NOT NULL,
            sharpe_ratio REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS backtest_predictions (
            run_id INTEGER NOT NULL,
            window_idx INTEGER NOT NULL,
            target_start_utc TEXT NOT NULL,
            context_end_utc TEXT NOT NULL,
            context_last_close REAL NOT NULL,
            predicted_step1_close REAL NOT NULL,
            actual_step1_close REAL NOT NULL,
            predicted_end_close REAL NOT NULL,
            actual_end_close REAL NOT NULL,
            predicted_return REAL NOT NULL,
            actual_return REAL NOT NULL,
            strategy_return REAL NOT NULL,
            direction_correct INTEGER NOT NULL,
            forecast_json TEXT NOT NULL,
            actual_json TEXT NOT NULL,
            PRIMARY KEY (run_id, window_idx),
            FOREIGN KEY (run_id) REFERENCES backtest_runs (run_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_candles_lookup
        ON candles (exchange, symbol, interval, open_time_ms)
        """
    )


def fetch_binance_klines(
    symbol: str,
    start_ms: int,
    end_ms: int,
    interval: str = "1m",
    limit: int = 1000,
) -> list[list]:
    all_rows: list[list] = []
    cursor = start_ms

    while cursor < end_ms:
        params = urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": limit,
            }
        )
        request = Request(
            f"{BINANCE_KLINES_URL}?{params}",
            headers={"User-Agent": "timesfm-fin/crypto-minute-backtest"},
        )
        with urlopen(request, timeout=30) as response:
            batch = json.loads(response.read().decode("utf-8"))

        if not isinstance(batch, list):
            raise ValueError(f"Unexpected Binance response: {batch!r}")
        if not batch:
            break

        all_rows.extend(batch)
        next_cursor = int(batch[-1][0]) + ONE_MINUTE_MS
        if next_cursor <= cursor:
            raise RuntimeError("Binance pagination stalled while fetching klines.")
        cursor = next_cursor

    unique_rows = {int(row[0]): row for row in all_rows}
    return [
        unique_rows[open_time]
        for open_time in sorted(unique_rows)
        if start_ms <= open_time < end_ms
    ]


def store_candles(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
    interval: str,
    rows: list[list],
) -> int:
    records = [
        (
            exchange,
            symbol,
            interval,
            int(row[0]),
            to_utc_iso(int(row[0])),
            int(row[6]),
            to_utc_iso(int(row[6])),
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4]),
            float(row[5]),
            float(row[7]),
            int(row[8]),
            float(row[9]),
            float(row[10]),
        )
        for row in rows
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO candles (
            exchange,
            symbol,
            interval,
            open_time_ms,
            open_time_utc,
            close_time_ms,
            close_time_utc,
            open,
            high,
            low,
            close,
            volume,
            quote_asset_volume,
            trades,
            taker_buy_base_volume,
            taker_buy_quote_volume
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )
    return len(records)


def load_candles(
    conn: sqlite3.Connection,
    exchange: str,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame:
    frame = pd.read_sql_query(
        """
        SELECT
            open_time_ms,
            open_time_utc,
            close
        FROM candles
        WHERE exchange = ?
          AND symbol = ?
          AND interval = ?
          AND open_time_ms >= ?
          AND open_time_ms < ?
        ORDER BY open_time_ms
        """,
        conn,
        params=(exchange, symbol, interval, start_ms, end_ms),
    )
    if frame.empty:
        raise ValueError("No candles found in SQLite for the requested period.")

    frame["open_time_utc"] = pd.to_datetime(frame["open_time_utc"], utc=True)
    frame["close"] = frame["close"].astype(float)
    return frame


def prepare_live_frame(
    conn: sqlite3.Connection,
    symbol: str,
    context_len: int,
) -> tuple[pd.DataFrame, datetime, datetime]:
    start_dt, end_dt = latest_closed_minute_bounds(context_len=context_len)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    fetched_rows = fetch_binance_klines(
        symbol=symbol,
        start_ms=start_ms,
        end_ms=end_ms,
        interval="1m",
    )
    if not fetched_rows:
        raise ValueError("No live candles returned from Binance.")

    with conn:
        store_candles(
            conn,
            exchange="binance",
            symbol=symbol,
            interval="1m",
            rows=fetched_rows,
        )

    frame = load_candles(
        conn,
        exchange="binance",
        symbol=symbol,
        interval="1m",
        start_ms=start_ms,
        end_ms=end_ms,
    )
    if len(frame) < context_len:
        raise ValueError(
            f"Need at least {context_len} live candles, got {len(frame)}."
        )
    return frame.tail(context_len).reset_index(drop=True), start_dt, end_dt


def annual_returns(returns: pd.Series, periods_per_year: float) -> float:
    clean_returns = returns.dropna().astype(float)
    if clean_returns.size < 2:
        return 0.0
    return float(clean_returns.mean() * periods_per_year)


def annualized_volatility(returns: pd.Series, periods_per_year: float) -> float:
    clean_returns = returns.dropna().astype(float)
    if clean_returns.size < 2:
        return 0.0
    return float(np.std(clean_returns.to_numpy(dtype=np.float64)) * math.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    periods_per_year: float,
    risk_free_rate: float = 0.0,
) -> float:
    ann_vol = annualized_volatility(returns, periods_per_year=periods_per_year)
    if ann_vol == 0.0:
        return 0.0
    ann_ret = annual_returns(returns, periods_per_year=periods_per_year)
    return float((ann_ret - risk_free_rate) / ann_vol)


def batched(values: list[int], batch_size: int) -> Iterable[list[int]]:
    for idx in range(0, len(values), batch_size):
        yield values[idx:idx + batch_size]


def select_independent_returns(
    strategy_returns: pd.Series,
    horizon_len: int,
    stride: int,
) -> tuple[pd.Series, int]:
    non_overlap_step = max(1, math.ceil(horizon_len / stride))
    independent_returns = strategy_returns.iloc[::non_overlap_step].reset_index(drop=True)
    return independent_returns, non_overlap_step


def run_backtest(
    model,
    frame: pd.DataFrame,
    context_len: int,
    horizon_len: int,
    stride: int,
    batch_size: int,
    max_windows: int | None,
    freq: int,
) -> tuple[dict[str, float | int], list[tuple]]:
    values = frame["close"].to_numpy(dtype=np.float64)
    timestamps = frame["open_time_utc"]

    if values.size < context_len + horizon_len + 1:
        raise ValueError(
            "Not enough candles for the requested setup. "
            f"Need at least {context_len + horizon_len + 1}, got {values.size}."
        )

    start_indices = list(range(context_len, values.size - horizon_len + 1, stride))
    if max_windows is not None:
        start_indices = start_indices[:max_windows]
    if not start_indices:
        raise ValueError("The chosen context/horizon/stride produced zero backtest windows.")

    prediction_rows: list[tuple] = []
    all_predictions: list[np.ndarray] = []
    all_actuals: list[np.ndarray] = []
    all_last_context: list[float] = []
    all_strategy_returns: list[float] = []
    all_direction_correct: list[int] = []

    for window_batch in batched(start_indices, batch_size=batch_size):
        contexts = [
            values[start - context_len:start].astype(np.float32)
            for start in window_batch
        ]
        predictions_batch, _ = model.forecast(contexts, freq=[freq] * len(window_batch))
        predictions_batch = np.asarray(predictions_batch, dtype=np.float64)

        for batch_offset, start in enumerate(window_batch):
            prediction = predictions_batch[batch_offset][:horizon_len]
            actual = values[start:start + horizon_len].astype(np.float64)
            last_context_close = float(values[start - 1])
            predicted_return = float((prediction[-1] - last_context_close) / last_context_close)
            actual_return = float((actual[-1] - last_context_close) / last_context_close)
            position = float(np.sign(predicted_return))
            strategy_return = float(position * actual_return)
            direction_correct = int(np.sign(predicted_return) == np.sign(actual_return))

            all_predictions.append(prediction)
            all_actuals.append(actual)
            all_last_context.append(last_context_close)
            all_strategy_returns.append(strategy_return)
            all_direction_correct.append(direction_correct)
            prediction_rows.append(
                (
                    len(prediction_rows),
                    timestamps.iloc[start].isoformat(),
                    timestamps.iloc[start - 1].isoformat(),
                    last_context_close,
                    float(prediction[0]),
                    float(actual[0]),
                    float(prediction[-1]),
                    float(actual[-1]),
                    predicted_return,
                    actual_return,
                    strategy_return,
                    direction_correct,
                    json.dumps(prediction.tolist()),
                    json.dumps(actual.tolist()),
                )
            )

    predictions = np.vstack(all_predictions)
    actuals = np.vstack(all_actuals)
    last_context = np.asarray(all_last_context, dtype=np.float64)
    strategy_returns = pd.Series(all_strategy_returns, dtype="float64")
    independent_returns, non_overlap_step = select_independent_returns(
        strategy_returns=strategy_returns,
        horizon_len=horizon_len,
        stride=stride,
    )
    effective_holding_minutes = stride * non_overlap_step
    effective_periods_per_year = MINUTES_PER_YEAR / effective_holding_minutes

    flat_predictions = predictions.reshape(-1)
    flat_actuals = actuals.reshape(-1)
    step1_predictions = predictions[:, 0]
    step1_actuals = actuals[:, 0]
    end_predictions = predictions[:, -1]
    end_actuals = actuals[:, -1]

    metrics = {
        "points": int(values.size),
        "windows": int(predictions.shape[0]),
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
        "hit_rate": float(np.mean(np.asarray(all_direction_correct, dtype=np.float64))),
        "strategy_mean_return": float(independent_returns.mean()),
        "strategy_std": float(independent_returns.std(ddof=0)),
        "annual_return": annual_returns(
            independent_returns, periods_per_year=effective_periods_per_year
        ),
        "annualized_volatility": annualized_volatility(
            independent_returns, periods_per_year=effective_periods_per_year
        ),
        "sharpe_ratio": sharpe_ratio(
            independent_returns, periods_per_year=effective_periods_per_year
        ),
    }
    return metrics, prediction_rows


def save_backtest(
    conn: sqlite3.Connection,
    args: argparse.Namespace,
    start_dt: datetime,
    end_dt: datetime,
    metrics: dict[str, float | int],
    prediction_rows: list[tuple],
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO backtest_runs (
            created_at_utc,
            exchange,
            symbol,
            interval,
            model_repo_id,
            backend,
            freq_bucket,
            context_len,
            horizon_len,
            stride,
            batch_size,
            data_start_utc,
            data_end_utc,
            points,
            windows,
            mae,
            rmse,
            mape_pct,
            smape_pct,
            step1_mae,
            step1_rmse,
            step1_directional_accuracy,
            end_directional_accuracy,
            hit_rate,
            strategy_mean_return,
            strategy_std,
            annual_return,
            annualized_volatility,
            sharpe_ratio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "binance",
            args.symbol,
            "1m",
            args.repo_id,
            args.backend,
            args.freq,
            args.context_len,
            args.horizon_len,
            args.stride,
            args.batch_size,
            start_dt.isoformat(),
            end_dt.isoformat(),
            metrics["points"],
            metrics["windows"],
            metrics["mae"],
            metrics["rmse"],
            metrics["mape_pct"],
            metrics["smape_pct"],
            metrics["step1_mae"],
            metrics["step1_rmse"],
            metrics["step1_directional_accuracy"],
            metrics["end_directional_accuracy"],
            metrics["hit_rate"],
            metrics["strategy_mean_return"],
            metrics["strategy_std"],
            metrics["annual_return"],
            metrics["annualized_volatility"],
            metrics["sharpe_ratio"],
        ),
    )
    run_id = int(cursor.lastrowid)

    conn.executemany(
        """
        INSERT INTO backtest_predictions (
            run_id,
            window_idx,
            target_start_utc,
            context_end_utc,
            context_last_close,
            predicted_step1_close,
            actual_step1_close,
            predicted_end_close,
            actual_end_close,
            predicted_return,
            actual_return,
            strategy_return,
            direction_correct,
            forecast_json,
            actual_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(run_id, *row) for row in prediction_rows],
    )
    return run_id


def build_live_forecast_table(
    frame: pd.DataFrame,
    forecast: np.ndarray,
) -> pd.DataFrame:
    last_timestamp = pd.Timestamp(frame["open_time_utc"].iloc[-1])
    future_index = pd.date_range(
        start=last_timestamp + pd.Timedelta(minutes=1),
        periods=len(forecast),
        freq="1min",
        tz="UTC",
    )
    latest_close = float(frame["close"].iloc[-1])
    return pd.DataFrame(
        {
            "ds": future_index,
            "step": np.arange(1, len(forecast) + 1, dtype=int),
            "forecast_close": forecast,
            "predicted_return_pct": ((forecast / latest_close) - 1.0) * 100.0,
        }
    )


def run_live_forecast(
    model,
    frame: pd.DataFrame,
    horizon_len: int,
    freq: int,
) -> tuple[pd.DataFrame, float]:
    context = frame["close"].to_numpy(dtype=np.float32)
    if context.size == 0:
        raise ValueError("No live context available for forecasting.")

    point_forecast, _ = model.forecast([context], freq=[freq])
    forecast = np.asarray(point_forecast[0], dtype=np.float64)[:horizon_len]
    latest_close = float(frame["close"].iloc[-1])
    forecast_df = build_live_forecast_table(frame=frame, forecast=forecast)
    return forecast_df, latest_close


def print_summary(
    args: argparse.Namespace,
    start_dt: datetime,
    end_dt: datetime,
    candle_count: int,
    metrics: dict[str, float | int],
    run_id: int,
) -> None:
    print(f"Exchange: Binance")
    print(f"Symbol: {args.symbol}")
    print(f"UTC day: {args.day.isoformat()} ({start_dt.isoformat()} to {end_dt.isoformat()})")
    print(f"Candles stored/read: {candle_count}")
    print(f"Run id: {run_id}")
    print("")
    print(f"Windows: {metrics['windows']}")
    print(f"MAE: {metrics['mae']:.6f}")
    print(f"RMSE: {metrics['rmse']:.6f}")
    print(f"MAPE (%): {metrics['mape_pct']:.6f}")
    print(f"SMAPE (%): {metrics['smape_pct']:.6f}")
    print(f"Step1 directional accuracy: {metrics['step1_directional_accuracy']:.6f}")
    print(f"End directional accuracy: {metrics['end_directional_accuracy']:.6f}")
    print(f"Hit rate: {metrics['hit_rate']:.6f}")
    print(f"Strategy mean return: {metrics['strategy_mean_return']:.8f}")
    print(f"Strategy return std: {metrics['strategy_std']:.8f}")
    print(f"Annual return: {metrics['annual_return']:.6f}")
    print(f"Annualized volatility: {metrics['annualized_volatility']:.6f}")
    print(f"Sharpe ratio: {metrics['sharpe_ratio']:.6f}")
    print("")
    print(f"SQLite database: {args.db_path.resolve()}")


def print_live_forecast(
    args: argparse.Namespace,
    frame: pd.DataFrame,
    latest_close: float,
    forecast_df: pd.DataFrame,
) -> None:
    context_start = pd.Timestamp(frame["open_time_utc"].iloc[0]).isoformat()
    context_end = pd.Timestamp(frame["open_time_utc"].iloc[-1]).isoformat()
    print("Exchange: Binance")
    print(f"Symbol: {args.symbol}")
    print("Mode: live")
    print(f"Context window: {context_start} to {context_end}")
    print(f"Context candles used: {len(frame)}")
    print(f"Latest observed close: {latest_close:.4f}")
    print("")
    print(forecast_df.to_string(index=False))

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        forecast_df.to_csv(args.output_csv, index=False)
        print("")
        print(f"Saved forecast to: {args.output_csv}")


def main() -> None:
    args = parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db_path)
    try:
        ensure_schema(conn)

        model = build_model(
            context_len=args.context_len,
            horizon_len=args.horizon_len,
            backend=args.backend,
            repo_id=args.repo_id,
        )

        if args.mode == "live":
            frame, start_dt, end_dt = prepare_live_frame(
                conn=conn,
                symbol=args.symbol,
                context_len=args.context_len,
            )
            forecast_df, latest_close = run_live_forecast(
                model=model,
                frame=frame,
                horizon_len=args.horizon_len,
                freq=args.freq,
            )
            print_live_forecast(
                args=args,
                frame=frame,
                latest_close=latest_close,
                forecast_df=forecast_df,
            )
        else:
            start_dt, end_dt = day_bounds_utc(args.day)
            start_ms = int(start_dt.timestamp() * 1000)
            end_ms = int(end_dt.timestamp() * 1000)

            fetched_rows = fetch_binance_klines(
                symbol=args.symbol,
                start_ms=start_ms,
                end_ms=end_ms,
                interval="1m",
            )
            with conn:
                store_candles(
                    conn,
                    exchange="binance",
                    symbol=args.symbol,
                    interval="1m",
                    rows=fetched_rows,
                )

            frame = load_candles(
                conn,
                exchange="binance",
                symbol=args.symbol,
                interval="1m",
                start_ms=start_ms,
                end_ms=end_ms,
            )

            metrics, prediction_rows = run_backtest(
                model=model,
                frame=frame,
                context_len=args.context_len,
                horizon_len=args.horizon_len,
                stride=args.stride,
                batch_size=args.batch_size,
                max_windows=args.max_windows,
                freq=args.freq,
            )

            with conn:
                run_id = save_backtest(
                    conn=conn,
                    args=args,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    metrics=metrics,
                    prediction_rows=prediction_rows,
                )

            print_summary(
                args=args,
                start_dt=start_dt,
                end_dt=end_dt,
                candle_count=len(frame),
                metrics=metrics,
                run_id=run_id,
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
