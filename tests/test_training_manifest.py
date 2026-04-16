from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from importlib import import_module

import pytest


pytestmark = pytest.mark.contract


def load_manifest_module():
    return pytest.importorskip("training_manifest")


def test_manifest_rejects_invalid_symbol_ranges_and_missing_holdouts() -> None:
    module = load_manifest_module()

    valid_symbol = {
        "symbol": "BTCUSDT",
        "train_start_utc": "2025-11-01T00:00:00Z",
        "train_end_utc": "2025-12-01T00:00:00Z",
        "holdout_start_utc": "2025-12-01T00:00:00Z",
        "holdout_end_utc": "2026-04-01T00:00:00Z",
    }
    valid = {
        "source_name": "binance",
        "timeframe": "1m",
        "preset": None,
        "window_length": 640,
        "stride": 128,
        "cleaning": {"mode": "strict", "repairable_gap_minutes": 5},
        "symbols": [valid_symbol],
    }

    normalized = module.validate_manifest(valid)
    assert normalized["symbols"][0]["symbol"] == "BTCUSDT"

    invalid_symbol = dict(valid_symbol, symbol="DOGEUSDT")
    with pytest.raises(ValueError, match="DOGEUSDT"):
        module.validate_manifest({**valid, "symbols": [invalid_symbol]})

    overlapping = dict(
        valid_symbol,
        holdout_start_utc="2025-11-20T00:00:00Z",
        holdout_end_utc="2026-04-01T00:00:00Z",
    )
    with pytest.raises(ValueError, match="overlap|Holdout"):
        module.validate_manifest({**valid, "symbols": [overlapping]})

    missing_holdout = dict(valid_symbol)
    missing_holdout.pop("holdout_end_utc")
    with pytest.raises(ValueError, match="holdout"):
        module.validate_manifest({**valid, "symbols": [missing_holdout]})


def test_starter_preset_builds_one_month_round_with_btc_four_month_reserve() -> None:
    module = load_manifest_module()
    reference_end = datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc)

    manifest = module.build_preset_manifest(
        "starter_1m",
        end_utc=reference_end,
    )
    by_symbol = {entry["symbol"]: entry for entry in manifest["symbols"]}

    assert sorted(by_symbol) == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    btc = by_symbol["BTCUSDT"]
    eth = by_symbol["ETHUSDT"]

    assert btc["holdout_end_utc"] == "2026-04-16T00:00:00Z"
    assert btc["holdout_start_utc"] == "2025-12-17T00:00:00Z"
    assert btc["train_end_utc"] == btc["holdout_start_utc"]
    assert btc["train_start_utc"] == "2025-11-17T00:00:00Z"
    assert eth["train_end_utc"] == eth["holdout_start_utc"]


def test_manifest_serialization_preserves_explicit_slice_choices(tmp_path) -> None:
    module = load_manifest_module()
    manifest = module.build_preset_manifest(
        "starter_1m",
        end_utc=datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc),
    )
    output_path = tmp_path / "training_manifest.json"

    module.write_manifest(manifest, output_path)
    loaded = module.load_manifest(output_path)
    serialized = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert loaded["symbols"] == manifest["symbols"]
    assert serialized["symbols"][0]["train_start_utc"].endswith("Z")
    assert serialized["cleaning"]["mode"] == "strict"
