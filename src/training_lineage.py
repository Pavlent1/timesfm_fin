from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_path(path: Path, label: str) -> Path:
    if not path.exists():
        raise ValueError(f"{label} is missing: {path}")
    return path


def load_run_manifest(run_dir: Path) -> dict[str, Any]:
    manifest_path = require_path(run_dir / "run_manifest.json", "run_manifest")
    manifest = read_json(manifest_path)
    if manifest.get("status") != "completed":
        raise ValueError(f"Run bundle is not complete: {run_dir}")
    return manifest


def validate_required_fields(manifest: dict[str, Any]) -> None:
    required_paths = (
        manifest.get("evaluation_summary_path"),
        manifest.get("backtest_summary_path"),
    )
    if not all(required_paths):
        raise ValueError(
            "Run bundle must reference both evaluation_summary.json and backtest_summary.json."
        )

    if not manifest.get("produced_checkpoint"):
        raise ValueError("Run bundle must record the produced checkpoint.")
    if not manifest.get("parent_checkpoint"):
        raise ValueError("Run bundle must record the parent checkpoint.")

    prepared_bundle = manifest.get("prepared_bundle", {})
    if not prepared_bundle.get("symbols"):
        raise ValueError("Run bundle must record explicit training and holdout ranges.")
    if not prepared_bundle.get("dataset_manifest_id"):
        raise ValueError("Run bundle must record the prepared bundle manifest identity.")
    if not manifest.get("training_config", {}).get("copied_path"):
        raise ValueError("Run bundle must record the copied training config path.")


def normalize_symbol_ranges(symbol_entries: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for entry in symbol_entries:
        normalized[str(entry["symbol"])] = {
            "train_start_utc": str(entry["train_start_utc"]),
            "train_end_utc": str(entry["train_end_utc"]),
            "holdout_start_utc": str(entry["holdout_start_utc"]),
            "holdout_end_utc": str(entry["holdout_end_utc"]),
        }
    return normalized


def build_lineage_manifest(run_dir: Path) -> dict[str, Any]:
    resolved_run_dir = run_dir.resolve()
    manifest = load_run_manifest(resolved_run_dir)
    validate_required_fields(manifest)

    evaluation_path = require_path(
        Path(manifest["evaluation_summary_path"]),
        "evaluation_summary",
    )
    backtest_path = require_path(
        Path(manifest["backtest_summary_path"]),
        "backtest_summary",
    )
    evaluation_summary = read_json(evaluation_path)
    backtest_summary = read_json(backtest_path)
    if not evaluation_summary:
        raise ValueError("evaluation_summary.json must contain real evaluation data.")
    if not backtest_summary:
        raise ValueError("backtest_summary.json must contain real backtest data.")

    prepared_bundle = manifest["prepared_bundle"]
    per_symbol_ranges = normalize_symbol_ranges(prepared_bundle["symbols"])
    selected_symbols = sorted(per_symbol_ranges)

    return {
        "run_name": manifest.get("run_name", resolved_run_dir.name),
        "run_dir": str(resolved_run_dir),
        "produced_checkpoint": manifest["produced_checkpoint"],
        "parent_checkpoint": manifest["parent_checkpoint"],
        "selected_symbols": selected_symbols,
        "dataset_manifest_id": prepared_bundle["dataset_manifest_id"],
        "sample_counts": prepared_bundle.get("sample_counts", {}),
        "preparer_settings": {
            "cleaning": prepared_bundle.get("cleaning", {}),
            "window_length": prepared_bundle.get("window_length"),
            "stride": prepared_bundle.get("stride"),
        },
        "training_config": manifest["training_config"],
        "per_symbol_ranges": per_symbol_ranges,
        "evaluation_summary": evaluation_summary,
        "backtest_summary": backtest_summary,
        "backtest_run_id": manifest.get("backtest_run_id") or backtest_summary.get("backtest_run_id"),
    }


def write_lineage_manifest(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    lineage = build_lineage_manifest(run_dir)
    target_path = output_path or (run_dir / "lineage_manifest.json")
    target_path.write_text(json.dumps(lineage, indent=2) + "\n", encoding="utf-8")
    return lineage
