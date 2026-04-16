from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

import pandas as pd

from postgres_dataset import connect_postgres, load_postgres_settings
from postgres_verify_data import load_observations
from training_manifest import (
    DEFAULT_STRIDE,
    DEFAULT_WINDOW_LENGTH,
    format_utc_datetime,
    load_manifest,
    manifest_identity,
    parse_utc_datetime,
    validate_manifest,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description="Prepare manifest-driven Phase 3 training bundles from PostgreSQL."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument("--password", default=defaults.password, help="Database password.")
    parser.add_argument("--manifest", type=Path, required=True, help="Training manifest JSON path.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Prepared bundle directory.")
    return parser.parse_args(argv)


def load_series_slice(
    conn,
    *,
    source_name: str,
    symbol: str,
    timeframe: str,
    start_utc,
    end_utc,
) -> pd.DataFrame:
    frame = load_observations(
        conn,
        source=source_name,
        symbol=symbol,
        timeframe=timeframe,
        start=start_utc,
        end=end_utc,
    )
    if frame.empty:
        raise ValueError(f"No PostgreSQL observations found for {symbol} in the selected range.")

    frame = frame.sort_values("observation_time_utc").reset_index(drop=True)
    return frame[["symbol", "observation_time_utc", "close_price"]].copy()


def find_missing_segments(series: pd.Series) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    is_missing = series.isna()
    start_index: int | None = None

    for index, missing in enumerate(is_missing):
        if missing and start_index is None:
            start_index = index
        if not missing and start_index is not None:
            gaps.append(
                {
                    "start_index": start_index,
                    "end_index": index - 1,
                    "missing_minutes": index - start_index,
                }
            )
            start_index = None

    if start_index is not None:
        gaps.append(
            {
                "start_index": start_index,
                "end_index": len(series) - 1,
                "missing_minutes": len(series) - start_index,
            }
        )

    return gaps


def clean_series_frame(
    frame: pd.DataFrame,
    *,
    mode: str,
    repairable_gap_minutes: int,
    symbol: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    indexed = frame.set_index("observation_time_utc")["close_price"].sort_index()
    expected_index = pd.date_range(
        start=indexed.index[0],
        end=indexed.index[-1],
        freq="1min",
        tz="UTC",
    )
    reindexed = indexed.reindex(expected_index)
    repairs: list[dict[str, object]] = []

    for gap in find_missing_segments(reindexed):
        if mode == "strict":
            raise ValueError(f"{symbol} contains a gap of {gap['missing_minutes']} minute(s).")

        touches_boundary = (
            gap["start_index"] == 0 or gap["end_index"] == len(reindexed) - 1
        )
        if gap["missing_minutes"] > repairable_gap_minutes or touches_boundary:
            raise ValueError(
                f"{symbol} has a blocking gap of {gap['missing_minutes']} minute(s)."
            )

        repairs.append(
            {
                "symbol": symbol,
                "missing_minutes": gap["missing_minutes"],
                "gap_start_utc": format_utc_datetime(expected_index[gap["start_index"]]),
                "gap_end_utc": format_utc_datetime(expected_index[gap["end_index"]]),
            }
        )

    if repairs:
        reindexed = reindexed.ffill()

    if reindexed.isna().any():
        raise ValueError(f"{symbol} still contains unrepaired missing values.")
    if (reindexed <= 0).any():
        raise ValueError(f"{symbol} contains non-positive values, which are unsafe for training.")

    cleaned = pd.DataFrame(
        {
            "symbol": symbol,
            "observation_time_utc": expected_index,
            "close_price": reindexed.to_numpy(),
        }
    )
    return cleaned, repairs


def build_windows(
    frame: pd.DataFrame,
    *,
    window_length: int,
    stride: int,
    symbol: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = frame["close_price"].tolist()
    timestamps = frame["observation_time_utc"].tolist()
    window_columns: dict[str, list[float]] = {}
    window_rows: list[dict[str, object]] = []
    window_number = 0

    for start_index in range(0, len(prices) - window_length + 1, stride):
        window_number += 1
        end_index = start_index + window_length
        window_id = f"{symbol.lower()}_{window_number:04d}"
        window_columns[window_id] = prices[start_index:end_index]
        window_rows.append(
            {
                "window_id": window_id,
                "symbol": symbol,
                "window_start_utc": format_utc_datetime(timestamps[start_index]),
                "window_end_utc": format_utc_datetime(timestamps[end_index - 1]),
                "point_count": window_length,
            }
        )

    if not window_columns:
        raise ValueError(
            f"{symbol} produced no {window_length}-point windows from the selected training slice."
        )

    return pd.DataFrame(window_columns), pd.DataFrame(window_rows)


def write_bundle_artifact(path: Path, content) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, pd.DataFrame):
        content.to_csv(path, index=False)
        return

    path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def prepare_training_bundle(
    conn,
    manifest: Mapping[str, object],
    output_dir: Path,
) -> dict[str, Path]:
    normalized = validate_manifest(manifest)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_windows_frames: list[pd.DataFrame] = []
    holdout_frames: list[pd.DataFrame] = []
    window_index_frames: list[pd.DataFrame] = []
    repairs: list[dict[str, object]] = []
    sample_counts: dict[str, int] = {}

    for symbol_entry in normalized["symbols"]:
        symbol = symbol_entry["symbol"]
        train_start = parse_utc_datetime(symbol_entry["train_start_utc"])
        train_end = parse_utc_datetime(symbol_entry["train_end_utc"])
        holdout_start = parse_utc_datetime(symbol_entry["holdout_start_utc"])
        holdout_end = parse_utc_datetime(symbol_entry["holdout_end_utc"])

        train_frame = load_series_slice(
            conn,
            source_name=normalized["source_name"],
            symbol=symbol,
            timeframe=normalized["timeframe"],
            start_utc=train_start,
            end_utc=train_end,
        )
        cleaned_train, train_repairs = clean_series_frame(
            train_frame,
            mode=normalized["cleaning"]["mode"],
            repairable_gap_minutes=normalized["cleaning"]["repairable_gap_minutes"],
            symbol=symbol,
        )
        holdout_frame = load_series_slice(
            conn,
            source_name=normalized["source_name"],
            symbol=symbol,
            timeframe=normalized["timeframe"],
            start_utc=holdout_start,
            end_utc=holdout_end,
        )
        cleaned_holdout, holdout_repairs = clean_series_frame(
            holdout_frame,
            mode=normalized["cleaning"]["mode"],
            repairable_gap_minutes=normalized["cleaning"]["repairable_gap_minutes"],
            symbol=symbol,
        )
        repairs.extend(train_repairs)
        repairs.extend(holdout_repairs)

        windows_frame, window_index = build_windows(
            cleaned_train,
            window_length=int(normalized.get("window_length", DEFAULT_WINDOW_LENGTH)),
            stride=int(normalized.get("stride", DEFAULT_STRIDE)),
            symbol=symbol,
        )
        train_windows_frames.append(windows_frame)
        window_index_frames.append(window_index)
        holdout_frames.append(cleaned_holdout)
        sample_counts[symbol] = windows_frame.shape[1]

    train_windows = pd.concat(train_windows_frames, axis=1)
    holdout_series = pd.concat(holdout_frames, ignore_index=True)
    window_index = pd.concat(window_index_frames, ignore_index=True)

    dataset_manifest = dict(normalized)
    dataset_manifest["manifest_id"] = manifest_identity(normalized)
    dataset_manifest["sample_counts"] = {
        "total": int(train_windows.shape[1]),
        "per_symbol": sample_counts,
    }

    quality_report = {
        "cleaning_mode": normalized["cleaning"]["mode"],
        "repairable_gap_minutes": normalized["cleaning"]["repairable_gap_minutes"],
        "repairs": repairs,
        "window_length": normalized["window_length"],
        "stride": normalized["stride"],
    }

    paths = {
        "train_windows_path": output_dir / "train_windows.csv",
        "holdout_series_path": output_dir / "holdout_series.csv",
        "dataset_manifest_path": output_dir / "dataset_manifest.json",
        "quality_report_path": output_dir / "quality_report.json",
        "window_index_path": output_dir / "window_index.csv",
    }
    write_bundle_artifact(paths["train_windows_path"], train_windows)
    write_bundle_artifact(paths["holdout_series_path"], holdout_series)
    write_bundle_artifact(paths["dataset_manifest_path"], dataset_manifest)
    write_bundle_artifact(paths["quality_report_path"], quality_report)
    write_bundle_artifact(paths["window_index_path"], window_index)
    return paths


def main() -> None:
    args = parse_args()
    settings = load_postgres_settings(
        {
            "POSTGRES_HOST": args.host,
            "POSTGRES_PORT": str(args.port),
            "POSTGRES_DB": args.db_name,
            "POSTGRES_USER": args.user,
            "POSTGRES_PASSWORD": args.password,
        }
    )
    manifest = load_manifest(args.manifest)

    with connect_postgres(settings=settings, autocommit=True) as conn:
        result = prepare_training_bundle(conn, manifest, args.output_dir)

    print(
        f"Prepared bundle: {args.output_dir}\n"
        f"Train windows: {result['train_windows_path']}\n"
        f"Holdout series: {result['holdout_series_path']}"
    )


if __name__ == "__main__":
    main()
