from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from backtest_metrics import build_step_metrics
from evaluate_training_run import (
    ForecastFn,
    build_symbol_windows,
    default_forecast_contexts,
    load_holdout_series,
)


PersistFn = Callable[..., int | None]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backtest a trained checkpoint against the explicit Phase 3 holdout series "
            "and write backtest_summary.json."
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
    parser.add_argument("--context-len", type=int, default=512, help="Backtest context length.")
    parser.add_argument("--horizon-len", type=int, default=128, help="Backtest horizon length.")
    parser.add_argument("--stride", type=int, default=128, help="Step size between backtest windows.")
    parser.add_argument(
        "--backend",
        default="cpu",
        choices=["cpu", "gpu", "tpu"],
        help="Backend used to load the TimesFM checkpoint.",
    )
    return parser.parse_args(argv)


def summarize_step_rows(step_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not step_rows:
        return []

    rows: list[dict[str, object]] = []
    frame = pd.DataFrame(step_rows)
    for step_index, step_frame in frame.groupby("step_index", sort=True):
        overshoots = step_frame.loc[
            step_frame["overshoot_label"] == "overshoot",
            "normalized_deviation_pct",
        ]
        undershoots = step_frame.loc[
            step_frame["overshoot_label"] == "undershoot",
            "normalized_deviation_pct",
        ]
        rows.append(
            {
                "step_index": int(step_index),
                "step_count": int(len(step_frame)),
                "avg_normalized_deviation_pct": float(step_frame["normalized_deviation_pct"].mean()),
                "stddev_normalized_deviation_pct": float(
                    step_frame["normalized_deviation_pct"].std(ddof=0)
                ),
                "avg_overshoot_deviation_pct": float(overshoots.mean()) if not overshoots.empty else 0.0,
                "avg_undershoot_deviation_pct": float(undershoots.mean()) if not undershoots.empty else 0.0,
                "match_count": int(step_frame["direction_guess_correct"].sum()),
                "avg_signed_deviation_pct": float(step_frame["signed_deviation_pct"].mean()),
                "direction_guess_accuracy_pct": float(
                    step_frame["direction_guess_correct"].mean() * 100.0
                ),
            }
        )
    return rows


def backtest_training_run(
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
    persist_symbol_backtest: PersistFn | None = None,
) -> dict[str, object]:
    frame = load_holdout_series(holdout_series_path)
    forecast_fn = forecast_contexts or default_forecast_contexts

    symbol_summaries: list[dict[str, object]] = []
    backtest_run_ids: dict[str, int] = {}
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

        step_rows: list[dict[str, object]] = []
        for window_index, window in enumerate(windows):
            actual = np.asarray(window["actual"], dtype=np.float64)
            prediction = np.asarray(predictions[window_index], dtype=np.float64)
            last_input_close = float(window["context"][-1])

            for step_index, (predicted_close, actual_close) in enumerate(zip(prediction, actual)):
                metrics = build_step_metrics(
                    last_input_close=last_input_close,
                    predicted_close=float(predicted_close),
                    actual_close=float(actual_close),
                )
                step_rows.append(
                    {
                        "window_index": window_index,
                        "step_index": step_index,
                        "target_time_utc": (
                            window["target_start_utc"] + pd.Timedelta(minutes=step_index)
                        ).isoformat(),
                        "last_input_close": last_input_close,
                        "predicted_close": float(predicted_close),
                        "actual_close": float(actual_close),
                        "normalized_deviation_pct": metrics["normalized_deviation_pct"],
                        "signed_deviation_pct": metrics["signed_deviation_pct"],
                        "overshoot_label": metrics["overshoot_label"],
                        "direction_guess_correct": metrics["direction_guess_correct"],
                    }
                )

        run_id: int | None = None
        if persist_symbol_backtest is not None:
            run_id = persist_symbol_backtest(
                symbol=symbol,
                symbol_frame=symbol_frame,
                step_rows=step_rows,
                checkpoint_reference=checkpoint_reference,
                checkpoint_kind=checkpoint_kind,
                context_len=context_len,
                horizon_len=horizon_len,
                stride=stride,
            )
            if run_id is not None:
                backtest_run_ids[symbol] = int(run_id)

        total_windows += len(windows)
        symbol_summaries.append(
            {
                "symbol": symbol,
                "window_count": len(windows),
                "point_count": len(step_rows),
                "holdout_start_utc": symbol_frame["observation_time_utc"].iloc[0].isoformat(),
                "holdout_end_utc": symbol_frame["observation_time_utc"].iloc[-1].isoformat(),
                "step_stats": summarize_step_rows(step_rows),
            }
        )

    first_run_id = next(iter(backtest_run_ids.values()), None)
    summary = {
        "checkpoint_reference": checkpoint_reference,
        "checkpoint_kind": checkpoint_kind,
        "holdout_series_path": str(holdout_series_path),
        "canonical_for_phase3_comparison": True,
        "supplemental_provenance_only": True,
        "context_len": context_len,
        "horizon_len": horizon_len,
        "stride": stride,
        "symbol_count": len(symbol_summaries),
        "window_count": total_windows,
        "backtest_run_id": first_run_id,
        "backtest_run_ids": backtest_run_ids,
        "symbol_summaries": symbol_summaries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = backtest_training_run(
        holdout_series_path=args.holdout_series,
        output_path=args.output,
        checkpoint_reference=args.checkpoint_reference,
        checkpoint_kind=args.checkpoint_kind,
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        stride=args.stride,
        backend=args.backend,
    )
    print(f"Saved backtest summary to: {args.output}")
    print(f"Backtest windows evaluated: {summary['window_count']}")


if __name__ == "__main__":
    main()
