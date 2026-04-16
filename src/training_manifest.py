from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping


SUPPORTED_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DEFAULT_SOURCE_NAME = "binance"
DEFAULT_TIMEFRAME = "1m"
DEFAULT_WINDOW_LENGTH = 640
DEFAULT_STRIDE = 128
DEFAULT_REPAIRABLE_GAP_MINUTES = 5
APPROXIMATE_DAYS_PER_MONTH = 30
DEFAULT_BTC_HOLDOUT_MONTHS = 4
DEFAULT_ALT_HOLDOUT_DAYS = 7


def parse_utc_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif len(value) == 10:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def months_before(end_utc: datetime, months: int) -> datetime:
    return end_utc - timedelta(days=months * APPROXIMATE_DAYS_PER_MONTH)


def days_before(end_utc: datetime, days: int) -> datetime:
    return end_utc - timedelta(days=days)


def normalize_symbol_entry(entry: Mapping[str, object]) -> dict[str, object]:
    symbol = str(entry["symbol"])
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(
            f"Unsupported symbol {symbol}. Supported symbols: {', '.join(SUPPORTED_SYMBOLS)}."
        )

    required_fields = (
        "train_start_utc",
        "train_end_utc",
        "holdout_start_utc",
        "holdout_end_utc",
    )
    for field in required_fields:
        if field not in entry:
            raise ValueError(f"Missing required holdout/train field: {field}.")

    train_start = parse_utc_datetime(entry["train_start_utc"])
    train_end = parse_utc_datetime(entry["train_end_utc"])
    holdout_start = parse_utc_datetime(entry["holdout_start_utc"])
    holdout_end = parse_utc_datetime(entry["holdout_end_utc"])

    if train_start >= train_end:
        raise ValueError(f"Train range is inverted for {symbol}.")
    if holdout_start >= holdout_end:
        raise ValueError(f"Holdout range is inverted for {symbol}.")
    if holdout_start < train_end:
        raise ValueError(f"Holdout range cannot overlap the training range for {symbol}.")

    return {
        "symbol": symbol,
        "train_start_utc": format_utc_datetime(train_start),
        "train_end_utc": format_utc_datetime(train_end),
        "holdout_start_utc": format_utc_datetime(holdout_start),
        "holdout_end_utc": format_utc_datetime(holdout_end),
    }


def validate_manifest(document: Mapping[str, object]) -> dict[str, object]:
    mode = str(document.get("cleaning", {}).get("mode", "strict"))
    if mode not in {"strict", "repair"}:
        raise ValueError("Cleaning mode must be 'strict' or 'repair'.")

    symbol_entries = [normalize_symbol_entry(entry) for entry in document["symbols"]]
    seen = set()
    for entry in symbol_entries:
        if entry["symbol"] in seen:
            raise ValueError(f"Duplicate manifest symbol: {entry['symbol']}.")
        seen.add(entry["symbol"])

    return {
        "source_name": str(document.get("source_name", DEFAULT_SOURCE_NAME)),
        "timeframe": str(document.get("timeframe", DEFAULT_TIMEFRAME)),
        "preset": document.get("preset"),
        "window_length": int(document.get("window_length", DEFAULT_WINDOW_LENGTH)),
        "stride": int(document.get("stride", DEFAULT_STRIDE)),
        "cleaning": {
            "mode": mode,
            "repairable_gap_minutes": int(
                document.get("cleaning", {}).get(
                    "repairable_gap_minutes",
                    DEFAULT_REPAIRABLE_GAP_MINUTES,
                )
            ),
        },
        "symbols": symbol_entries,
    }


def build_preset_manifest(
    preset: str,
    *,
    end_utc: datetime,
    source_name: str = DEFAULT_SOURCE_NAME,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> dict[str, object]:
    if preset != "starter_1m":
        raise ValueError(f"Unsupported preset {preset}.")

    resolved_end = parse_utc_datetime(end_utc)
    entries: list[dict[str, object]] = []
    for symbol in SUPPORTED_SYMBOLS:
        if symbol == "BTCUSDT":
            holdout_end = resolved_end
            holdout_start = months_before(holdout_end, DEFAULT_BTC_HOLDOUT_MONTHS)
        else:
            holdout_end = resolved_end
            holdout_start = days_before(holdout_end, DEFAULT_ALT_HOLDOUT_DAYS)

        train_end = holdout_start
        train_start = months_before(train_end, 1)
        entries.append(
            {
                "symbol": symbol,
                "train_start_utc": format_utc_datetime(train_start),
                "train_end_utc": format_utc_datetime(train_end),
                "holdout_start_utc": format_utc_datetime(holdout_start),
                "holdout_end_utc": format_utc_datetime(holdout_end),
            }
        )

    return validate_manifest(
        {
            "source_name": source_name,
            "timeframe": timeframe,
            "preset": preset,
            "window_length": DEFAULT_WINDOW_LENGTH,
            "stride": DEFAULT_STRIDE,
            "cleaning": {
                "mode": "strict",
                "repairable_gap_minutes": DEFAULT_REPAIRABLE_GAP_MINUTES,
            },
            "symbols": entries,
        }
    )


def manifest_identity(manifest: Mapping[str, object]) -> str:
    serialized = json.dumps(validate_manifest(manifest), sort_keys=True).encode("utf-8")
    return sha256(serialized).hexdigest()[:16]


def write_manifest(manifest: Mapping[str, object], output_path: Path) -> None:
    normalized = validate_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(normalized, indent=2) + "\n",
        encoding="utf-8",
    )


def load_manifest(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return validate_manifest(document)
