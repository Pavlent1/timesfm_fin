from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import psycopg

from backtest_metrics import (
    DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT,
    absolute_move_pct_from_input,
    build_step_metrics,
)
from binance_market_data import fetch_binance_klines
from postgres_backtest import (
    create_backtest_run,
    create_backtest_window,
    insert_backtest_steps,
    query_backtest_step_stats,
)
from postgres_dataset import (
    PostgresSettings,
    connect_postgres,
    ensure_series,
    finalize_ingestion_run,
    load_postgres_settings,
    start_ingestion_run,
    upsert_observations,
)
from run_forecast import DEFAULT_REPO_ID, build_model


DEFAULT_SOURCE_NAME = "binance"
DEFAULT_TIMEFRAME = "1m"
BINANCE_SOURCE_ENDPOINT = "https://api.binance.com/api/v3/klines"
CONDITIONAL_DIRECTION_THRESHOLD_REPORT_SOURCE = (
    "outputs/backtests/followup_stats_btcusdt_2026-03-16_31d_next5.txt"
)
CONDITIONAL_DIRECTION_REPORT_COLUMNS = [
    "step_ahead",
    "threshold_basis",
    "threshold_band",
    "threshold_pct",
    "total_windows",
    "qualified_windows",
    "qualified_share_pct",
    "qualified_correct_count",
    "qualified_accuracy_pct",
    "non_qualified_accuracy_pct",
    "overall_accuracy_pct",
    "accuracy_lift_vs_overall_pct_points",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description=(
            "Read Binance 1-minute candles from PostgreSQL and run either "
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
        "--host",
        default=defaults.host,
        help="PostgreSQL host for the canonical market-data store.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=defaults.port,
        help="PostgreSQL port for the canonical market-data store.",
    )
    parser.add_argument(
        "--db-name",
        default=defaults.db_name,
        help="PostgreSQL database name for the canonical market-data store.",
    )
    parser.add_argument(
        "--user",
        default=defaults.user,
        help="PostgreSQL user for the canonical market-data store.",
    )
    parser.add_argument(
        "--password",
        default=defaults.password,
        help="PostgreSQL password for the canonical market-data store.",
    )
    parser.add_argument(
        "--symbol",
        default="BTCUSDT",
        help="Binance spot symbol to read or fetch. Default: BTCUSDT.",
    )
    parser.add_argument(
        "--day",
        type=parse_utc_day,
        default=default_previous_utc_day(),
        help=(
            "UTC start day to backtest in YYYY-MM-DD format. "
            "Default: the previous UTC day."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help=(
            "How many consecutive UTC days to backtest starting at --day. "
            "Use 1 for a single day or a larger value for multi-day runs."
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
        "--checkpoint-path",
        default=None,
        help="Optional local TimesFM checkpoint path. Overrides --repo-id when provided.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV output path for live forecasts.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=None,
        help=(
            "Optional text output path for backtest results. "
            "If omitted, backtest mode writes a default report under outputs/backtests/."
        ),
    )
    return parser.parse_args(argv)


def postgres_settings_from_args(args: argparse.Namespace) -> PostgresSettings:
    return load_postgres_settings(
        {
            "POSTGRES_HOST": args.host,
            "POSTGRES_PORT": str(args.port),
            "POSTGRES_DB": args.db_name,
            "POSTGRES_USER": args.user,
            "POSTGRES_PASSWORD": args.password,
        }
    )


def parse_utc_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_previous_utc_day() -> date:
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()


def day_bounds_utc(target_day: date, days: int = 1) -> tuple[datetime, datetime]:
    if days < 1:
        raise ValueError("--days must be at least 1.")
    start_dt = datetime.combine(target_day, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=days)
    return start_dt, end_dt


def latest_closed_minute_bounds(context_len: int) -> tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    end_dt = now_utc
    start_dt = end_dt - timedelta(minutes=context_len)
    return start_dt, end_dt


def normalize_close_observations(rows: list[list]) -> list[tuple[datetime, float]]:
    return [
        (
            datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
            float(row[4]),
        )
        for row in rows
    ]


def load_frame_range(
    conn: psycopg.Connection,
    *,
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                o.observation_time_utc,
                o.close_price
            FROM market_data.series AS s
            JOIN market_data.assets AS a ON a.asset_id = s.asset_id
            JOIN market_data.observations AS o ON o.series_id = s.series_id
            WHERE a.symbol = %s
              AND s.source_name = %s
              AND s.timeframe = %s
              AND s.field_name = 'close_price'
              AND o.observation_time_utc >= %s
              AND o.observation_time_utc < %s
            ORDER BY o.observation_time_utc
            """,
            (symbol, source_name, timeframe, start_dt, end_dt),
        )
        rows = cur.fetchall()

    if not rows:
        raise ValueError(
            "No PostgreSQL candles found for the requested period. "
            "Ingest or persist the Binance data first."
        )

    return pd.DataFrame(
        {
            "open_time_utc": pd.to_datetime([row[0] for row in rows], utc=True),
            "close": [float(row[1]) for row in rows],
        }
    )


def load_backtest_frame(
    conn: psycopg.Connection,
    *,
    symbol: str,
    target_day: date,
    days: int,
    context_len: int,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> pd.DataFrame:
    start_dt, end_dt = day_bounds_utc(target_day, days=days)
    query_start_dt = start_dt - timedelta(minutes=context_len)
    return load_frame_range(
        conn=conn,
        symbol=symbol,
        start_dt=query_start_dt,
        end_dt=end_dt,
        source_name=source_name,
        timeframe=timeframe,
    )


def persist_binance_rows(
    conn: psycopg.Connection,
    *,
    symbol: str,
    rows: list[list],
    requested_start_utc: datetime,
    requested_end_utc: datetime,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> int:
    series_id = ensure_series(
        conn=conn,
        symbol=symbol,
        source_name=source_name,
        timeframe=timeframe,
    )
    ingestion_run_id = start_ingestion_run(
        conn=conn,
        series_id=series_id,
        source_endpoint=BINANCE_SOURCE_ENDPOINT,
        requested_start_utc=requested_start_utc,
        requested_end_utc=requested_end_utc,
        notes={"symbol": symbol, "timeframe": timeframe, "mode": "live"},
    )
    observations = normalize_close_observations(rows)
    actual_start_utc = observations[0][0] if observations else None
    actual_end_utc = observations[-1][0] if observations else None
    rows_written = upsert_observations(
        conn=conn,
        series_id=series_id,
        ingestion_run_id=ingestion_run_id,
        observations=observations,
    )
    finalize_ingestion_run(
        conn=conn,
        ingestion_run_id=ingestion_run_id,
        actual_start_utc=actual_start_utc,
        actual_end_utc=actual_end_utc,
        rows_written=rows_written,
        status="completed" if observations else "empty",
        notes={"symbol": symbol, "timeframe": timeframe, "mode": "live"},
    )
    return rows_written


def prepare_live_frame(
    conn: psycopg.Connection,
    symbol: str,
    context_len: int,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> tuple[pd.DataFrame, datetime, datetime]:
    start_dt, end_dt = latest_closed_minute_bounds(context_len=context_len)

    fetched_rows = fetch_binance_klines(
        symbol=symbol,
        start_ms=int(start_dt.timestamp() * 1000),
        end_ms=int(end_dt.timestamp() * 1000),
        interval=timeframe,
    )
    if not fetched_rows:
        raise ValueError("No live candles returned from Binance.")

    persist_binance_rows(
        conn=conn,
        symbol=symbol,
        rows=fetched_rows,
        requested_start_utc=start_dt,
        requested_end_utc=end_dt,
        source_name=source_name,
        timeframe=timeframe,
    )
    conn.commit()

    frame = load_frame_range(
        conn=conn,
        symbol=symbol,
        start_dt=start_dt,
        end_dt=end_dt,
        source_name=source_name,
        timeframe=timeframe,
    )
    if len(frame) < context_len:
        raise ValueError(
            f"Need at least {context_len} live candles, got {len(frame)}."
        )
    return frame.tail(context_len).reset_index(drop=True), start_dt, end_dt


def batched(values: list[int], batch_size: int) -> Iterable[list[int]]:
    for idx in range(0, len(values), batch_size):
        yield values[idx : idx + batch_size]


def run_backtest(
    model,
    frame: pd.DataFrame,
    context_len: int,
    horizon_len: int,
    stride: int,
    batch_size: int,
    max_windows: int | None,
    freq: int,
) -> tuple[dict[str, float | int], list[dict[str, object]]]:
    values = frame["close"].to_numpy(dtype=np.float64)
    timestamps = pd.to_datetime(frame["open_time_utc"], utc=True)

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

    window_rows: list[dict[str, object]] = []

    for window_batch in batched(start_indices, batch_size=batch_size):
        contexts = [
            values[start - context_len : start].astype(np.float32)
            for start in window_batch
        ]
        predictions_batch, _ = model.forecast(contexts, freq=[freq] * len(window_batch))
        predictions_batch = np.asarray(predictions_batch, dtype=np.float64)

        for batch_offset, start in enumerate(window_batch):
            prediction = predictions_batch[batch_offset][:horizon_len]
            actual = values[start : start + horizon_len].astype(np.float64)
            last_context_close = float(values[start - 1])

            step_rows: list[dict[str, object]] = []
            for step_offset, (predicted_close, actual_close) in enumerate(
                zip(prediction, actual)
            ):
                step_metrics = build_step_metrics(
                    last_input_close=last_context_close,
                    predicted_close=float(predicted_close),
                    actual_close=float(actual_close),
                )
                step_rows.append(
                    {
                        "step_index": step_offset,
                        "target_time_utc": pd.Timestamp(
                            timestamps.iloc[start + step_offset]
                        ),
                        "last_input_close": last_context_close,
                        "predicted_close": float(predicted_close),
                        "actual_close": float(actual_close),
                        "normalized_deviation_pct": step_metrics[
                            "normalized_deviation_pct"
                        ],
                        "signed_deviation_pct": step_metrics["signed_deviation_pct"],
                        "overshoot_label": step_metrics["overshoot_label"],
                        "direction_guess_correct": step_metrics[
                            "direction_guess_correct"
                        ],
                    }
                )

            window_rows.append(
                {
                    "window_index": len(window_rows),
                    "target_start_utc": pd.Timestamp(timestamps.iloc[start]),
                    "context_end_utc": pd.Timestamp(timestamps.iloc[start - 1]),
                    "last_input_close": last_context_close,
                    "steps": step_rows,
                }
            )

    metrics = {
        "points": int(values.size),
        "windows": int(len(window_rows)),
    }
    return metrics, window_rows


def save_backtest(
    conn: psycopg.Connection,
    args: argparse.Namespace,
    start_dt: datetime,
    end_dt: datetime,
    metrics: dict[str, float | int],
    window_rows: list[dict[str, object]],
) -> int:
    run_id = create_backtest_run(
        conn=conn,
        exchange=DEFAULT_SOURCE_NAME,
        symbol=args.symbol,
        interval=DEFAULT_TIMEFRAME,
        model_repo_id=resolve_model_reference(args),
        backend=args.backend,
        freq_bucket=args.freq,
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        stride=args.stride,
        batch_size=args.batch_size,
        data_start_utc=start_dt,
        data_end_utc=end_dt,
        points=int(metrics["points"]),
        windows=int(metrics["windows"]),
    )

    for window_row in window_rows:
        window_id = create_backtest_window(
            conn=conn,
            run_id=run_id,
            window_index=int(window_row["window_index"]),
            target_start_utc=window_row["target_start_utc"].to_pydatetime(),
            context_end_utc=window_row["context_end_utc"].to_pydatetime(),
            last_input_close=float(window_row["last_input_close"]),
        )
        insert_backtest_steps(
            conn=conn,
            rows=[
                {
                    "run_id": run_id,
                    "window_id": window_id,
                    "step_index": int(step_row["step_index"]),
                    "target_time_utc": step_row["target_time_utc"].to_pydatetime(),
                    "last_input_close": float(step_row["last_input_close"]),
                    "predicted_close": float(step_row["predicted_close"]),
                    "actual_close": float(step_row["actual_close"]),
                    "normalized_deviation_pct": float(
                        step_row["normalized_deviation_pct"]
                    ),
                    "signed_deviation_pct": float(step_row["signed_deviation_pct"]),
                    "overshoot_label": str(step_row["overshoot_label"]),
                }
                for step_row in window_row["steps"]
            ],
        )

    return run_id


def default_backtest_report_path(run_id: int) -> Path:
    return Path("outputs") / "backtests" / f"run_{run_id}.txt"


def resolve_model_reference(args: argparse.Namespace) -> str:
    checkpoint_path = getattr(args, "checkpoint_path", None)
    if checkpoint_path:
        return str(checkpoint_path)
    return str(args.repo_id)


def flatten_backtest_step_rows(
    window_rows: list[dict[str, object]],
) -> list[dict[str, float | int]]:
    flattened_rows: list[dict[str, float | int]] = []

    for window_row in window_rows:
        for step_row in window_row["steps"]:
            step_ahead = int(step_row["step_index"]) + 1
            last_input_close = float(step_row["last_input_close"])
            predicted_close = float(step_row["predicted_close"])
            actual_close = float(step_row["actual_close"])
            flattened_rows.append(
                {
                    "step_ahead": step_ahead,
                    "actual_move_pct": absolute_move_pct_from_input(
                        last_input_close=last_input_close,
                        close_value=actual_close,
                    ),
                    "predicted_move_pct": absolute_move_pct_from_input(
                        last_input_close=last_input_close,
                        close_value=predicted_close,
                    ),
                    "direction_guess_correct": int(step_row["direction_guess_correct"]),
                }
            )

    return flattened_rows


def accuracy_pct(rows: list[dict[str, float | int]]) -> float:
    if not rows:
        return float(np.nan)
    correct_count = sum(int(row["direction_guess_correct"]) for row in rows)
    return (correct_count / len(rows)) * 100.0


def qualified_share_pct(qualified_windows: int, total_windows: int) -> float:
    if total_windows == 0:
        return 0.0
    return (qualified_windows / total_windows) * 100.0


def build_conditional_direction_accuracy_rows(
    window_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    flattened_rows = flatten_backtest_step_rows(window_rows)
    conditional_rows: list[dict[str, object]] = []

    for step_ahead, thresholds in DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT.items():
        step_rows = [
            row for row in flattened_rows if int(row["step_ahead"]) == step_ahead
        ]
        total_windows = len(step_rows)
        overall_accuracy = accuracy_pct(step_rows)

        for threshold_basis in ("actual_move_pct", "predicted_move_pct"):
            for threshold_band, threshold_key in (
                ("lower", "lower_threshold_pct"),
                ("upper", "upper_threshold_pct"),
            ):
                threshold_pct = float(thresholds[threshold_key])
                qualified_rows = [
                    row for row in step_rows if float(row[threshold_basis]) >= threshold_pct
                ]
                non_qualified_rows = [
                    row for row in step_rows if float(row[threshold_basis]) < threshold_pct
                ]
                qualified_accuracy = accuracy_pct(qualified_rows)
                non_qualified_accuracy = accuracy_pct(non_qualified_rows)

                conditional_rows.append(
                    {
                        "step_ahead": step_ahead,
                        "threshold_basis": threshold_basis,
                        "threshold_band": threshold_band,
                        "threshold_pct": threshold_pct,
                        "total_windows": total_windows,
                        "qualified_windows": len(qualified_rows),
                        "qualified_share_pct": qualified_share_pct(
                            len(qualified_rows),
                            total_windows,
                        ),
                        "qualified_correct_count": sum(
                            int(row["direction_guess_correct"])
                            for row in qualified_rows
                        ),
                        "qualified_accuracy_pct": qualified_accuracy,
                        "non_qualified_accuracy_pct": non_qualified_accuracy,
                        "overall_accuracy_pct": overall_accuracy,
                        "accuracy_lift_vs_overall_pct_points": (
                            qualified_accuracy - overall_accuracy
                            if qualified_rows and not np.isnan(overall_accuracy)
                            else float(np.nan)
                        ),
                    }
                )

    return conditional_rows


def render_backtest_report(
    *,
    args: argparse.Namespace,
    requested_start_dt: datetime,
    requested_end_dt: datetime,
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    metrics: dict[str, float | int],
    run_id: int,
    step_stats_rows: list[dict[str, object]],
    conditional_stats_rows: list[dict[str, object]],
) -> str:
    lines = [
        "TimesFM Crypto Backtest Report",
        "",
        f"Run id: {run_id}",
        f"Exchange: Binance",
        f"Symbol: {args.symbol}",
        f"Requested UTC start: {requested_start_dt.isoformat()}",
        f"Requested UTC end: {requested_end_dt.isoformat()}",
        f"Requested days: {args.days}",
        f"Context length: {args.context_len}",
        f"Horizon length: {args.horizon_len}",
        f"Stride: {args.stride}",
        f"Batch size: {args.batch_size}",
        f"Backend: {args.backend}",
        (
            f"Checkpoint path: {args.checkpoint_path}"
            if getattr(args, "checkpoint_path", None)
            else f"Repo id: {args.repo_id}"
        ),
        f"Frequency bucket: {args.freq}",
        f"Loaded candles: {loaded_candle_count}",
        f"Requested-range candles: {evaluation_candle_count}",
        f"Context-lookback candles: {lookback_candle_count}",
        f"Forecast windows: {int(metrics['windows'])}",
        f"PostgreSQL: {args.host}:{args.port}/{args.db_name}",
        "",
        "Per-step stats (market_data.backtest_step_stats_vw)",
    ]

    if step_stats_rows:
        stats_frame = pd.DataFrame(step_stats_rows)
        lines.append(stats_frame.to_string(index=False))
    else:
        lines.append("No per-step stats found for this run.")

    lines.extend(
        [
            "",
            "Conditional direction accuracy by move threshold",
            (
                "Threshold source: "
                f"{CONDITIONAL_DIRECTION_THRESHOLD_REPORT_SOURCE}"
            ),
        ]
    )

    if conditional_stats_rows:
        conditional_frame = pd.DataFrame(
            conditional_stats_rows,
            columns=CONDITIONAL_DIRECTION_REPORT_COLUMNS,
        )
        lines.append(
            conditional_frame.to_string(
                index=False,
                float_format=lambda value: f"{value:.6f}",
            )
        )
    else:
        lines.append("No conditional direction stats found for this run.")

    lines.append("")
    return "\n".join(lines)


def write_backtest_report(path: Path, report_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text, encoding="utf-8")


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
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    metrics: dict[str, float | int],
    run_id: int,
    report_path: Path,
) -> None:
    window_count = int(metrics["windows"])
    print("Exchange: Binance")
    print(f"Symbol: {args.symbol}")
    if args.days == 1:
        print(
            f"Requested UTC day: {args.day.isoformat()} "
            f"({start_dt.isoformat()} to {end_dt.isoformat()})"
        )
    else:
        print(
            f"Requested UTC range: {args.day.isoformat()} + {args.days} days "
            f"({start_dt.isoformat()} to {end_dt.isoformat()})"
        )
    if lookback_candle_count > 0:
        print(
            "Candles read from PostgreSQL: "
            f"{loaded_candle_count} total "
            f"({evaluation_candle_count} in requested range, "
            f"{lookback_candle_count} context lookback)"
        )
    else:
        print(f"Candles read from PostgreSQL: {loaded_candle_count}")
    print(f"Backtest run id: {run_id}")
    print("")
    if window_count == 1:
        print("Forecast windows evaluated: 1 (one forecast block)")
    else:
        print(f"Forecast windows evaluated: {window_count}")
    print("")
    print(f"PostgreSQL: {args.host}:{args.port}/{args.db_name}")
    print("Per-step stats view: market_data.backtest_step_stats_vw")
    print(f"Saved report: {report_path}")


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
    print(f"PostgreSQL: {args.host}:{args.port}/{args.db_name}")
    print("")
    print(forecast_df.to_string(index=False))

    if args.output_csv is not None:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        forecast_df.to_csv(args.output_csv, index=False)
        print("")
        print(f"Saved forecast to: {args.output_csv}")


def main() -> None:
    args = parse_args()
    settings = postgres_settings_from_args(args)

    model = build_model(
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        backend=args.backend,
        repo_id=args.repo_id,
        checkpoint_path=getattr(args, "checkpoint_path", None),
    )

    with connect_postgres(settings=settings, autocommit=False) as conn:
        if args.mode == "live":
            frame, _, _ = prepare_live_frame(
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
            return

        requested_start_dt, requested_end_dt = day_bounds_utc(
            args.day,
            days=args.days,
        )
        frame = load_backtest_frame(
            conn=conn,
            symbol=args.symbol,
            target_day=args.day,
            days=args.days,
            context_len=args.context_len,
        )
        metrics, window_rows = run_backtest(
            model=model,
            frame=frame,
            context_len=args.context_len,
            horizon_len=args.horizon_len,
            stride=args.stride,
            batch_size=args.batch_size,
            max_windows=args.max_windows,
            freq=args.freq,
        )
        evaluation_mask = (
            (frame["open_time_utc"] >= pd.Timestamp(requested_start_dt))
            & (frame["open_time_utc"] < pd.Timestamp(requested_end_dt))
        )
        evaluation_candle_count = int(evaluation_mask.sum())
        lookback_candle_count = len(frame) - evaluation_candle_count
        coverage_start_dt = pd.Timestamp(frame["open_time_utc"].iloc[0]).to_pydatetime()
        coverage_end_dt = pd.Timestamp(frame["open_time_utc"].iloc[-1]).to_pydatetime()
        run_id = save_backtest(
            conn=conn,
            args=args,
            start_dt=coverage_start_dt,
            end_dt=coverage_end_dt,
            metrics=metrics,
            window_rows=window_rows,
        )
        report_path = args.output_report or default_backtest_report_path(run_id)
        step_stats_rows = query_backtest_step_stats(conn=conn, run_id=run_id)
        conditional_stats_rows = build_conditional_direction_accuracy_rows(
            window_rows=window_rows
        )
        report_text = render_backtest_report(
            args=args,
            requested_start_dt=requested_start_dt,
            requested_end_dt=requested_end_dt,
            loaded_candle_count=len(frame),
            evaluation_candle_count=evaluation_candle_count,
            lookback_candle_count=lookback_candle_count,
            metrics=metrics,
            run_id=run_id,
            step_stats_rows=step_stats_rows,
            conditional_stats_rows=conditional_stats_rows,
        )
        write_backtest_report(report_path, report_text)
        conn.commit()

        print_summary(
            args=args,
            start_dt=requested_start_dt,
            end_dt=requested_end_dt,
            loaded_candle_count=len(frame),
            evaluation_candle_count=evaluation_candle_count,
            lookback_candle_count=lookback_candle_count,
            metrics=metrics,
            run_id=run_id,
            report_path=report_path,
        )


if __name__ == "__main__":
    main()
