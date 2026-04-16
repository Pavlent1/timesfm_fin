from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import fmean, pstdev
from typing import Callable, Sequence

import pandas as pd

from backtest_metrics import build_step_metrics
from binance_market_data import fetch_binance_klines


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crypto_prediction_algo_export.btc_microstructure_model import (  # noqa: E402
    BtcMicrostructure,
    Candle,
    IndicatorSignals,
    MarketSnapshot,
    SignalEvaluation,
    evaluate_market,
)


DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_HISTORY_LEN = 60
DEFAULT_FUTURE_CANDLES = 5
DEFAULT_STRIDE = 1
DEFAULT_UP_PRICE = 0.5
DEFAULT_DOWN_PRICE = 0.5
MIN_HISTORY_LEN = 20


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the exported BTC microstructure strategy on historical "
            "Binance 1-minute candles and write a comparison-friendly report."
        )
    )
    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help="Binance spot symbol to backtest. Default: BTCUSDT.",
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
        "--history-len",
        type=int,
        default=DEFAULT_HISTORY_LEN,
        help=(
            "How many 1-minute candles to feed into the strategy at each "
            f"decision point. Minimum: {MIN_HISTORY_LEN}."
        ),
    )
    parser.add_argument(
        "--future-candles",
        type=int,
        default=DEFAULT_FUTURE_CANDLES,
        help="How many 1-minute candles ahead to score per decision point.",
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=None,
        help=(
            "Optional synthetic market duration for the exported time filter. "
            "Defaults to --future-candles."
        ),
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=DEFAULT_STRIDE,
        help="Step size between decision points.",
    )
    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="Optional cap on evaluated windows, useful for smoke tests.",
    )
    parser.add_argument(
        "--up-price",
        type=float,
        default=DEFAULT_UP_PRICE,
        help=(
            "Synthetic UP-side market price used by the exported strategy. "
            "Default: 0.50."
        ),
    )
    parser.add_argument(
        "--down-price",
        type=float,
        default=DEFAULT_DOWN_PRICE,
        help=(
            "Synthetic DOWN-side market price used by the exported strategy. "
            "Default: 0.50."
        ),
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=None,
        help=(
            "Optional text output path for the strategy report. "
            "If omitted, a default report is written under outputs/backtests/."
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional CSV path for per-window and per-step detail rows.",
    )
    return parser.parse_args(argv)


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


def resolve_window_minutes(args: argparse.Namespace) -> int:
    window_minutes = args.window_minutes or args.future_candles
    if window_minutes < 1:
        raise ValueError("--window-minutes must be at least 1.")
    return window_minutes


def requested_day_label(target_day: date, days: int) -> str:
    if days == 1:
        return target_day.isoformat()

    end_day = target_day + timedelta(days=days - 1)
    return f"{target_day.isoformat()}_to_{end_day.isoformat()}"


def normalize_binance_klines(rows: list[list]) -> list[Candle]:
    candles: list[Candle] = []
    for row in rows:
        candles.append(
            Candle(
                timestamp=datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
        )
    return candles


def load_backtest_candles(
    *,
    symbol: str,
    target_day: date,
    days: int,
    history_len: int,
    interval: str = DEFAULT_INTERVAL,
) -> tuple[list[Candle], datetime, datetime]:
    requested_start_dt, requested_end_dt = day_bounds_utc(target_day, days=days)
    query_start_dt = requested_start_dt - timedelta(minutes=history_len)
    rows = fetch_binance_klines(
        symbol=symbol,
        start_ms=int(query_start_dt.timestamp() * 1000),
        end_ms=int(requested_end_dt.timestamp() * 1000),
        interval=interval,
    )
    if not rows:
        raise ValueError("No Binance candles were returned for the requested period.")
    return normalize_binance_klines(rows), requested_start_dt, requested_end_dt


def classify_price_direction(*, baseline_close: float, future_close: float) -> str:
    if future_close > baseline_close:
        return "up"
    if future_close < baseline_close:
        return "down"
    return "match"


def realized_return_pct(*, baseline_close: float, future_close: float) -> float:
    if baseline_close == 0.0:
        raise ValueError("baseline_close must be non-zero.")
    return ((future_close / baseline_close) - 1.0) * 100.0


def build_market_snapshot(
    *,
    symbol: str,
    decision_time: datetime,
    window_minutes: int,
    up_price: float,
    down_price: float,
) -> MarketSnapshot:
    window_end = decision_time + timedelta(minutes=window_minutes)
    timestamp_slug = int(decision_time.timestamp())
    return MarketSnapshot(
        market_id=f"{symbol.lower()}-{timestamp_slug}",
        slug=f"{symbol.lower()}-updown-{window_minutes}m-{timestamp_slug}",
        up_price=up_price,
        down_price=down_price,
        window_end=window_end,
    )


def clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def blended_momentum_pct(microstructure: BtcMicrostructure) -> float:
    return (
        microstructure.momentum_1m * 0.50
        + microstructure.momentum_5m * 0.35
        + microstructure.momentum_15m * 0.15
    )


def project_return_pct(
    *,
    signal: SignalEvaluation,
    step_ahead: int,
) -> float:
    microstructure = signal.microstructure
    indicators: IndicatorSignals | None = signal.indicators

    if microstructure is None:
        probability_strength = clip((signal.model_up_probability - 0.5) / 0.15, -1.0, 1.0)
        return clip(probability_strength * 0.01 * step_ahead, -5.0, 5.0)

    raw_momentum_pct = blended_momentum_pct(microstructure)
    magnitude_anchor_pct = max(
        abs(raw_momentum_pct),
        abs(microstructure.vwap_deviation),
        abs(microstructure.sma_crossover),
        microstructure.volatility,
        0.01,
    )
    probability_strength = clip((signal.model_up_probability - 0.5) / 0.15, -1.0, 1.0)
    composite_strength = (
        clip(indicators.composite, -1.0, 1.0)
        if indicators is not None
        else probability_strength
    )
    directional_strength = (probability_strength * 0.7) + (composite_strength * 0.3)
    projected_return_pct = directional_strength * magnitude_anchor_pct * step_ahead
    return clip(projected_return_pct, -5.0, 5.0)


def project_future_close(
    *,
    signal: SignalEvaluation,
    baseline_close: float,
    step_ahead: int,
) -> float:
    projected_return = project_return_pct(signal=signal, step_ahead=step_ahead)
    return baseline_close * (1.0 + (projected_return / 100.0))


def average_labeled_deviation_pct(
    records: Sequence[dict[str, object]],
    *,
    label: str,
) -> float:
    matching_values = [
        float(record["normalized_deviation_pct"])
        for record in records
        if record["overshoot_label"] == label
    ]
    if not matching_values:
        return 0.0
    return fmean(matching_values)


def run_backtest(
    *,
    symbol: str,
    candles: Sequence[Candle],
    history_len: int,
    future_candles: int,
    stride: int,
    up_price: float,
    down_price: float,
    window_minutes: int,
    max_windows: int | None = None,
    evaluator: Callable[..., SignalEvaluation] = evaluate_market,
) -> tuple[dict[str, int], list[dict[str, float | int]], list[dict[str, object]]]:
    if history_len < MIN_HISTORY_LEN:
        raise ValueError(
            f"--history-len must be at least {MIN_HISTORY_LEN} for the exported model."
        )
    if future_candles < 1:
        raise ValueError("--future-candles must be at least 1.")
    if stride < 1:
        raise ValueError("--stride must be at least 1.")
    if not 0.0 <= up_price <= 1.0:
        raise ValueError("--up-price must be between 0.0 and 1.0.")
    if not 0.0 <= down_price <= 1.0:
        raise ValueError("--down-price must be between 0.0 and 1.0.")
    if up_price + down_price <= 0.0:
        raise ValueError("--up-price and --down-price must not both be zero.")
    if len(candles) < history_len + future_candles:
        raise ValueError(
            "Not enough candles for the requested setup. "
            f"Need at least {history_len + future_candles}, got {len(candles)}."
        )

    start_indices = list(range(history_len, len(candles) - future_candles + 1, stride))
    if max_windows is not None:
        start_indices = start_indices[:max_windows]
    if not start_indices:
        raise ValueError(
            "The chosen history/future-candles/stride produced zero analysis windows."
        )

    step_detail_rows: list[list[dict[str, object]]] = [[] for _ in range(future_candles)]
    detail_rows: list[dict[str, object]] = []
    invalid_windows = 0

    for start_index in start_indices:
        context = list(candles[start_index - history_len : start_index])
        decision_candle = context[-1]
        decision_time = decision_candle.timestamp
        baseline_close = float(decision_candle.close)
        market = build_market_snapshot(
            symbol=symbol,
            decision_time=decision_time,
            window_minutes=window_minutes,
            up_price=up_price,
            down_price=down_price,
        )
        signal = evaluator(
            market=market,
            candles=context,
            now=decision_time,
        )
        if not signal.valid:
            invalid_windows += 1
            continue

        for step_offset in range(future_candles):
            future_candle = candles[start_index + step_offset]
            future_close = float(future_candle.close)
            predicted_close = project_future_close(
                signal=signal,
                baseline_close=baseline_close,
                step_ahead=step_offset + 1,
            )
            step_metrics = build_step_metrics(
                last_input_close=baseline_close,
                predicted_close=predicted_close,
                actual_close=future_close,
            )
            detail_row = {
                "decision_time_utc": decision_time.isoformat(),
                "target_time_utc": future_candle.timestamp.isoformat(),
                "step_index": step_offset,
                "last_input_close": baseline_close,
                "predicted_close": predicted_close,
                "actual_close": future_close,
                "normalized_deviation_pct": step_metrics["normalized_deviation_pct"],
                "signed_deviation_pct": step_metrics["signed_deviation_pct"],
                "overshoot_label": step_metrics["overshoot_label"],
                "direction_guess_correct": step_metrics["direction_guess_correct"],
                "actionable": signal.actionable,
                "passes_filters": signal.passes_filters,
                "passes_threshold": signal.passes_threshold,
                "model_up_probability_pct": signal.model_up_probability * 100.0,
                "market_up_probability_pct": signal.market_up_probability * 100.0,
                "raw_edge_pct": signal.raw_edge * 100.0,
                "confidence_pct": signal.confidence * 100.0,
                "composite_signal": (
                    signal.indicators.composite if signal.indicators is not None else None
                ),
                "projected_return_pct": project_return_pct(
                    signal=signal,
                    step_ahead=step_offset + 1,
                ),
            }
            detail_rows.append(detail_row)
            step_detail_rows[step_offset].append(detail_row)

    valid_windows = len(start_indices) - invalid_windows
    if valid_windows == 0:
        raise ValueError(
            "The strategy produced zero valid evaluation windows. "
            "Try increasing --history-len or adjusting the synthetic market prices."
        )

    step_stats_rows: list[dict[str, float | int]] = []
    for step_offset in range(future_candles):
        records = step_detail_rows[step_offset]
        normalized_values = [
            float(record["normalized_deviation_pct"]) for record in records
        ]
        signed_values = [float(record["signed_deviation_pct"]) for record in records]
        direction_guess_values = [
            int(record["direction_guess_correct"]) for record in records
        ]
        match_count = sum(1 for record in records if record["overshoot_label"] == "match")

        step_stats_rows.append(
            {
                "step_index": step_offset,
                "step_count": len(records),
                "avg_normalized_deviation_pct": fmean(normalized_values),
                "stddev_normalized_deviation_pct": pstdev(normalized_values),
                "avg_overshoot_deviation_pct": average_labeled_deviation_pct(
                    records,
                    label="overshoot",
                ),
                "avg_undershoot_deviation_pct": average_labeled_deviation_pct(
                    records,
                    label="undershoot",
                ),
                "match_count": match_count,
                "avg_signed_deviation_pct": fmean(signed_values),
                "direction_guess_accuracy_pct": fmean(direction_guess_values) * 100.0,
            }
        )

    metrics = {
        "points": len(candles),
        "requested_windows": len(start_indices),
        "valid_windows": valid_windows,
        "invalid_windows": invalid_windows,
        "history_len": history_len,
        "future_candles": future_candles,
    }
    return metrics, step_stats_rows, detail_rows


def default_report_path(args: argparse.Namespace) -> Path:
    requested_label = requested_day_label(args.day, args.days)
    return (
        Path("outputs")
        / "backtests"
        / f"crypto_prediction_backtest_{args.symbol.lower()}_{requested_label}_next{args.future_candles}.txt"
    )


def render_report(
    *,
    args: argparse.Namespace,
    requested_start_dt: datetime,
    requested_end_dt: datetime,
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    window_minutes: int,
    metrics: dict[str, int],
    step_stats_rows: list[dict[str, float | int]],
) -> str:
    lines = [
        "Crypto Prediction Strategy Backtest Report",
        "",
        "Strategy: btc_microstructure_model.evaluate_market",
        "Data source: Binance spot klines",
        f"Symbol: {args.symbol}",
        f"Requested UTC start: {requested_start_dt.isoformat()}",
        f"Requested UTC end: {requested_end_dt.isoformat()}",
        f"Requested days: {args.days}",
        f"History length: {metrics['history_len']}",
        f"Horizon length: {metrics['future_candles']}",
        f"Synthetic market window minutes: {window_minutes}",
        f"Stride: {args.stride}",
        f"Synthetic UP price: {args.up_price:.4f}",
        f"Synthetic DOWN price: {args.down_price:.4f}",
        f"Loaded candles: {loaded_candle_count}",
        f"Requested-range candles: {evaluation_candle_count}",
        f"Context-lookback candles: {lookback_candle_count}",
        f"Forecast windows: {metrics['valid_windows']}",
        f"Invalid windows skipped: {metrics['invalid_windows']}",
        "",
        "Per-step stats",
    ]

    if step_stats_rows:
        stats_frame = pd.DataFrame(step_stats_rows)
        lines.append(stats_frame.to_string(index=False))
    else:
        lines.append("No per-step stats were produced.")

    lines.extend(
        [
            "",
            "Notes",
            (
                "- Predicted close values are synthesized from the export's own "
                "composite signal and recent microstructure magnitude so the "
                "strategy can be scored with the same deviation metrics as the "
                "TimesFM backtest."
            ),
            (
                "- Synthetic market prices default to a neutral 50/50 snapshot. "
                "Override --up-price/--down-price if you want the strategy filters "
                "to reflect a different implied market."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path, report_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text, encoding="utf-8")


def write_detail_csv(path: Path, detail_rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "decision_time_utc",
        "target_time_utc",
        "step_index",
        "last_input_close",
        "predicted_close",
        "actual_close",
        "normalized_deviation_pct",
        "signed_deviation_pct",
        "overshoot_label",
        "direction_guess_correct",
        "actionable",
        "passes_filters",
        "passes_threshold",
        "model_up_probability_pct",
        "market_up_probability_pct",
        "raw_edge_pct",
        "confidence_pct",
        "composite_signal",
        "projected_return_pct",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detail_rows)


def print_summary(
    *,
    args: argparse.Namespace,
    requested_start_dt: datetime,
    requested_end_dt: datetime,
    loaded_candle_count: int,
    evaluation_candle_count: int,
    lookback_candle_count: int,
    metrics: dict[str, int],
    report_path: Path,
    detail_csv_path: Path | None,
) -> None:
    print("Strategy: btc_microstructure_model.evaluate_market")
    print(f"Symbol: {args.symbol}")
    if args.days == 1:
        print(
            f"Requested UTC day: {args.day.isoformat()} "
            f"({requested_start_dt.isoformat()} to {requested_end_dt.isoformat()})"
        )
    else:
        print(
            f"Requested UTC range: {args.day.isoformat()} + {args.days} days "
            f"({requested_start_dt.isoformat()} to {requested_end_dt.isoformat()})"
        )
    print(
        "Candles read from Binance: "
        f"{loaded_candle_count} total "
        f"({evaluation_candle_count} in requested range, "
        f"{lookback_candle_count} context lookback)"
    )
    print(f"Forecast windows: {metrics['valid_windows']}")
    print(f"Invalid windows skipped: {metrics['invalid_windows']}")
    print("")
    print(f"Saved report: {report_path}")
    if detail_csv_path is not None:
        print(f"Saved detail CSV: {detail_csv_path}")


def main() -> None:
    args = parse_args()
    window_minutes = resolve_window_minutes(args)
    candles, requested_start_dt, requested_end_dt = load_backtest_candles(
        symbol=args.symbol,
        target_day=args.day,
        days=args.days,
        history_len=args.history_len,
    )
    metrics, step_stats_rows, detail_rows = run_backtest(
        symbol=args.symbol,
        candles=candles,
        history_len=args.history_len,
        future_candles=args.future_candles,
        stride=args.stride,
        up_price=args.up_price,
        down_price=args.down_price,
        window_minutes=window_minutes,
        max_windows=args.max_windows,
    )

    evaluation_candle_count = sum(
        1
        for candle in candles
        if requested_start_dt <= candle.timestamp < requested_end_dt
    )
    lookback_candle_count = len(candles) - evaluation_candle_count

    report_path = args.output_report or default_report_path(args)
    report_text = render_report(
        args=args,
        requested_start_dt=requested_start_dt,
        requested_end_dt=requested_end_dt,
        loaded_candle_count=len(candles),
        evaluation_candle_count=evaluation_candle_count,
        lookback_candle_count=lookback_candle_count,
        window_minutes=window_minutes,
        metrics=metrics,
        step_stats_rows=step_stats_rows,
    )
    write_report(report_path, report_text)

    detail_csv_path = args.output_csv
    if detail_csv_path is not None:
        write_detail_csv(detail_csv_path, detail_rows)

    print_summary(
        args=args,
        requested_start_dt=requested_start_dt,
        requested_end_dt=requested_end_dt,
        loaded_candle_count=len(candles),
        evaluation_candle_count=evaluation_candle_count,
        lookback_candle_count=lookback_candle_count,
        metrics=metrics,
        report_path=report_path,
        detail_csv_path=detail_csv_path,
    )


if __name__ == "__main__":
    main()
