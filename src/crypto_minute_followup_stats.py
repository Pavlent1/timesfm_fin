from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

from backtest_metrics import normalized_deviation_pct
from postgres_dataset import PostgresSettings, connect_postgres, load_postgres_settings


DEFAULT_SOURCE_NAME = "binance"
DEFAULT_TIMEFRAME = "1m"
DEFAULT_LOOKBACK_CANDLES = 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description=(
            "Read Binance 1-minute candles from PostgreSQL and analyze how the "
            "next N candles move relative to the original candle, without "
            "running the model."
        )
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
        help="Binance spot symbol to analyze. Default: BTCUSDT.",
    )
    parser.add_argument(
        "--day",
        type=parse_utc_day,
        default=default_previous_utc_day(),
        help=(
            "UTC start day to analyze in YYYY-MM-DD format. "
            "Default: the previous UTC day."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help=(
            "How many consecutive UTC days to analyze starting at --day. "
            "Use 1 for a single day or a larger value for multi-day runs."
        ),
    )
    parser.add_argument(
        "--future-candles",
        type=int,
        default=5,
        help="How many 1-minute candles after the original candle to analyze.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Step size between analyzed windows.",
    )
    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="Optional cap on rolling windows, useful for quick smoke tests.",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=None,
        help=(
            "Optional text output path for the candle-followup report. "
            "If omitted, a default report is written under outputs/backtests/."
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
            "Ingest the Binance data first."
        )

    return pd.DataFrame(
        {
            "open_time_utc": pd.to_datetime([row[0] for row in rows], utc=True),
            "close": [float(row[1]) for row in rows],
        }
    )


def load_analysis_frame(
    conn: psycopg.Connection,
    *,
    symbol: str,
    target_day: date,
    days: int,
    lookback_candles: int = DEFAULT_LOOKBACK_CANDLES,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> pd.DataFrame:
    start_dt, end_dt = day_bounds_utc(target_day, days=days)
    query_start_dt = start_dt - timedelta(minutes=lookback_candles)
    return load_frame_range(
        conn=conn,
        symbol=symbol,
        start_dt=query_start_dt,
        end_dt=end_dt,
        source_name=source_name,
        timeframe=timeframe,
    )


def classify_relative_close(*, baseline_close: float, future_close: float) -> str:
    if future_close > baseline_close:
        return "above"
    if future_close < baseline_close:
        return "below"
    return "match"


def run_followup_analysis(
    frame: pd.DataFrame,
    *,
    lookback_candles: int = DEFAULT_LOOKBACK_CANDLES,
    future_candles: int = 5,
    stride: int = 1,
    max_windows: int | None = None,
) -> tuple[dict[str, int], list[dict[str, float | int]]]:
    if lookback_candles < 1:
        raise ValueError("lookback_candles must be at least 1.")
    if future_candles < 1:
        raise ValueError("--future-candles must be at least 1.")
    if stride < 1:
        raise ValueError("--stride must be at least 1.")

    values = frame["close"].to_numpy(dtype=np.float64)

    if values.size < lookback_candles + future_candles:
        raise ValueError(
            "Not enough candles for the requested setup. "
            f"Need at least {lookback_candles + future_candles}, got {values.size}."
        )

    start_indices = list(
        range(lookback_candles, values.size - future_candles + 1, stride)
    )
    if max_windows is not None:
        start_indices = start_indices[:max_windows]
    if not start_indices:
        raise ValueError(
            "The chosen lookback/future-candles/stride produced zero analysis windows."
        )

    step_records: list[list[dict[str, float | str]]] = [[] for _ in range(future_candles)]

    for start in start_indices:
        baseline_close = float(values[start - 1])
        for step_offset in range(future_candles):
            future_close = float(values[start + step_offset])
            close_difference = future_close - baseline_close
            step_records[step_offset].append(
                {
                    "relative_close": classify_relative_close(
                        baseline_close=baseline_close,
                        future_close=future_close,
                    ),
                    "close_difference": close_difference,
                    "normalized_deviation_pct": normalized_deviation_pct(
                        predicted_close=baseline_close,
                        actual_close=future_close,
                    ),
                }
            )

    step_stats_rows: list[dict[str, float | int]] = []
    for step_offset, records in enumerate(step_records):
        step_count = len(records)
        relative_labels = [str(record["relative_close"]) for record in records]
        close_differences = np.asarray(
            [float(record["close_difference"]) for record in records],
            dtype=np.float64,
        )
        normalized_deviations = np.asarray(
            [float(record["normalized_deviation_pct"]) for record in records],
            dtype=np.float64,
        )
        above_count = sum(label == "above" for label in relative_labels)
        below_count = sum(label == "below" for label in relative_labels)
        match_count = sum(label == "match" for label in relative_labels)

        step_stats_rows.append(
            {
                "step_ahead": step_offset + 1,
                "step_count": step_count,
                "above_count": above_count,
                "below_count": below_count,
                "match_count": match_count,
                "above_pct": (above_count / step_count) * 100.0,
                "below_pct": (below_count / step_count) * 100.0,
                "match_pct": (match_count / step_count) * 100.0,
                "avg_close_difference": float(close_differences.mean()),
                "avg_abs_close_difference": float(np.abs(close_differences).mean()),
                "avg_normalized_deviation_pct": float(normalized_deviations.mean()),
                "stddev_normalized_deviation_pct": float(
                    normalized_deviations.std(ddof=0)
                ),
            }
        )

    metrics = {
        "points": int(values.size),
        "windows": int(len(start_indices)),
        "lookback_candles": int(lookback_candles),
        "future_candles": int(future_candles),
    }
    return metrics, step_stats_rows


def default_report_path(args: argparse.Namespace) -> Path:
    days_suffix = (
        args.day.isoformat() if args.days == 1 else f"{args.day.isoformat()}_{args.days}d"
    )
    return (
        Path("outputs")
        / "backtests"
        / f"followup_stats_{args.symbol.lower()}_{days_suffix}_next{args.future_candles}.txt"
    )


def render_followup_report(
    *,
    args: argparse.Namespace,
    requested_start_dt: datetime,
    requested_end_dt: datetime,
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    metrics: dict[str, int],
    step_stats_rows: list[dict[str, float | int]],
) -> str:
    lines = [
        "Crypto Minute Candle Follow-up Stats Report",
        "",
        "Exchange: Binance",
        f"Symbol: {args.symbol}",
        f"Requested UTC start: {requested_start_dt.isoformat()}",
        f"Requested UTC end: {requested_end_dt.isoformat()}",
        f"Requested days: {args.days}",
        f"Reference candles per window: {metrics['lookback_candles']}",
        f"Future candles per window: {metrics['future_candles']}",
        f"Stride: {args.stride}",
        f"Loaded candles: {loaded_candle_count}",
        f"Requested-range candles: {evaluation_candle_count}",
        f"Context-lookback candles: {lookback_candle_count}",
        f"Analysis windows: {metrics['windows']}",
        f"PostgreSQL: {args.host}:{args.port}/{args.db_name}",
        "",
        "Per-step stats",
    ]

    if step_stats_rows:
        stats_frame = pd.DataFrame(step_stats_rows)
        lines.append(stats_frame.to_string(index=False))
    else:
        lines.append("No per-step stats found for this run.")

    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, report_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text, encoding="utf-8")


def print_summary(
    args: argparse.Namespace,
    start_dt: datetime,
    end_dt: datetime,
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    metrics: dict[str, int],
    report_path: Path,
) -> None:
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
    print(
        f"Reference candle + future candles: "
        f"{metrics['lookback_candles']} + {metrics['future_candles']}"
    )
    print(f"Analysis windows: {metrics['windows']}")
    print("")
    print(f"PostgreSQL: {args.host}:{args.port}/{args.db_name}")
    print(f"Saved report: {report_path}")


def main() -> None:
    args = parse_args()
    settings = postgres_settings_from_args(args)
    requested_start_dt, requested_end_dt = day_bounds_utc(args.day, days=args.days)

    with connect_postgres(settings=settings, autocommit=False) as conn:
        frame = load_analysis_frame(
            conn=conn,
            symbol=args.symbol,
            target_day=args.day,
            days=args.days,
            lookback_candles=DEFAULT_LOOKBACK_CANDLES,
        )
        metrics, step_stats_rows = run_followup_analysis(
            frame=frame,
            lookback_candles=DEFAULT_LOOKBACK_CANDLES,
            future_candles=args.future_candles,
            stride=args.stride,
            max_windows=args.max_windows,
        )

    evaluation_mask = (
        (frame["open_time_utc"] >= pd.Timestamp(requested_start_dt))
        & (frame["open_time_utc"] < pd.Timestamp(requested_end_dt))
    )
    evaluation_candle_count = int(evaluation_mask.sum())
    lookback_candle_count = len(frame) - evaluation_candle_count
    report_path = args.output_report or default_report_path(args)
    report_text = render_followup_report(
        args=args,
        requested_start_dt=requested_start_dt,
        requested_end_dt=requested_end_dt,
        loaded_candle_count=len(frame),
        evaluation_candle_count=evaluation_candle_count,
        lookback_candle_count=lookback_candle_count,
        metrics=metrics,
        step_stats_rows=step_stats_rows,
    )
    write_report(report_path, report_text)

    print_summary(
        args=args,
        start_dt=requested_start_dt,
        end_dt=requested_end_dt,
        loaded_candle_count=len(frame),
        evaluation_candle_count=evaluation_candle_count,
        lookback_candle_count=lookback_candle_count,
        metrics=metrics,
        report_path=report_path,
    )


if __name__ == "__main__":
    main()
