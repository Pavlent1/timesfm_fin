from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract


def load_training_lineage_module():
    return pytest.importorskip("training_lineage")


def load_compare_training_runs_module():
    return pytest.importorskip("compare_training_runs")


def create_run_bundle(
    tmp_path: Path,
    *,
    name: str,
    parent_checkpoint: str,
    manifest_id: str,
    btc_train_start: str,
    btc_train_end: str,
    btc_holdout_start: str,
    btc_holdout_end: str,
    backtest_run_id: int,
    evaluation_mae: float,
) -> Path:
    run_dir = tmp_path / name
    run_dir.mkdir()
    evaluation_summary_path = run_dir / "evaluation_summary.json"
    backtest_summary_path = run_dir / "backtest_summary.json"

    evaluation_summary_path.write_text(
        json.dumps(
            {
                "canonical_for_phase3_comparison": True,
                "window_count": 4,
                "point_count": 8,
                "overall_metrics": {"mae": evaluation_mae, "rmse": evaluation_mae, "mape_pct": 1.0},
            }
        ),
        encoding="utf-8",
    )
    backtest_summary_path.write_text(
        json.dumps(
            {
                "canonical_for_phase3_comparison": True,
                "supplemental_provenance_only": True,
                "backtest_run_id": backtest_run_id,
                "backtest_run_ids": {"BTCUSDT": backtest_run_id},
                "symbol_summaries": [
                    {
                        "symbol": "BTCUSDT",
                        "step_stats": [
                            {
                                "step_index": 0,
                                "avg_normalized_deviation_pct": 1.5,
                                "direction_guess_accuracy_pct": 75.0,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "environment_snapshot.json").write_text(
        json.dumps({"manual_only": True}),
        encoding="utf-8",
    )
    (run_dir / "inputs").mkdir()
    (run_dir / "inputs" / "fine_tuning.py").write_text("config.batch_size = 8\n", encoding="utf-8")
    (run_dir / "holdout_series.csv").write_text("symbol,observation_time_utc,close_price\n", encoding="utf-8")

    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "phase": "03",
                "status": "completed",
                "run_name": name,
                "run_dir": str(run_dir),
                "produced_checkpoint": {"kind": "local_path", "value": str(run_dir)},
                "parent_checkpoint": {"kind": "repo", "value": parent_checkpoint},
                "prepared_bundle": {
                    "dataset_manifest_id": manifest_id,
                    "holdout_series_path": str(run_dir / "holdout_series.csv"),
                    "sample_counts": {"total": 12, "per_symbol": {"BTCUSDT": 12}},
                    "symbols": [
                        {
                            "symbol": "BTCUSDT",
                            "train_start_utc": btc_train_start,
                            "train_end_utc": btc_train_end,
                            "holdout_start_utc": btc_holdout_start,
                            "holdout_end_utc": btc_holdout_end,
                        }
                    ],
                    "cleaning": {"mode": "strict", "repairable_gap_minutes": 5},
                    "window_length": 640,
                    "stride": 128,
                },
                "training_config": {
                    "source_path": "configs/fine_tuning.py",
                    "copied_path": str(run_dir / "inputs" / "fine_tuning.py"),
                    "source_sha256": "abc",
                    "copied_sha256": "def",
                    "requested_batch_size": 1024,
                    "effective_batch_size": 8,
                },
                "environment": {"snapshot_path": str(run_dir / "environment_snapshot.json")},
                "evaluation_summary_path": str(evaluation_summary_path),
                "backtest_summary_path": str(backtest_summary_path),
                "backtest_run_id": backtest_run_id,
            }
        ),
        encoding="utf-8",
    )
    return run_dir


def test_lineage_manifest_requires_real_eval_and_backtest_artifacts(tmp_path) -> None:
    module = load_training_lineage_module()
    run_dir = tmp_path / "incomplete-run"
    run_dir.mkdir()
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "run_name": "incomplete-run",
                "produced_checkpoint": {"kind": "local_path", "value": str(run_dir)},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evaluation_summary|backtest_summary"):
        module.write_lineage_manifest(run_dir)


def test_lineage_manifest_normalizes_required_d17_fields(tmp_path) -> None:
    module = load_training_lineage_module()
    run_dir = create_run_bundle(
        tmp_path,
        name="run-a",
        parent_checkpoint="pfnet/timesfm-1.0-200m-fin",
        manifest_id="bundle-a",
        btc_train_start="2025-11-17T00:00:00Z",
        btc_train_end="2025-12-17T00:00:00Z",
        btc_holdout_start="2025-12-17T00:00:00Z",
        btc_holdout_end="2026-04-16T00:00:00Z",
        backtest_run_id=11,
        evaluation_mae=1.2,
    )

    lineage = module.write_lineage_manifest(run_dir)
    saved = json.loads((run_dir / "lineage_manifest.json").read_text(encoding="utf-8"))

    assert lineage["run_name"] == "run-a"
    assert saved["produced_checkpoint"]["value"] == str(run_dir)
    assert saved["parent_checkpoint"]["value"] == "pfnet/timesfm-1.0-200m-fin"
    assert saved["selected_symbols"] == ["BTCUSDT"]
    assert saved["evaluation_summary"]["overall_metrics"]["mae"] == pytest.approx(1.2)
    assert saved["backtest_summary"]["backtest_run_id"] == 11
    assert saved["per_symbol_ranges"]["BTCUSDT"]["holdout_end_utc"] == "2026-04-16T00:00:00Z"


def test_compare_training_runs_highlights_dataset_holdout_and_parent_differences(tmp_path) -> None:
    module = load_compare_training_runs_module()
    run_a = create_run_bundle(
        tmp_path,
        name="run-a",
        parent_checkpoint="pfnet/timesfm-1.0-200m-fin",
        manifest_id="bundle-a",
        btc_train_start="2025-11-17T00:00:00Z",
        btc_train_end="2025-12-17T00:00:00Z",
        btc_holdout_start="2025-12-17T00:00:00Z",
        btc_holdout_end="2026-04-16T00:00:00Z",
        backtest_run_id=11,
        evaluation_mae=1.2,
    )
    run_b = create_run_bundle(
        tmp_path,
        name="run-b",
        parent_checkpoint="runs/run-a",
        manifest_id="bundle-b",
        btc_train_start="2025-10-17T00:00:00Z",
        btc_train_end="2025-12-17T00:00:00Z",
        btc_holdout_start="2025-12-18T00:00:00Z",
        btc_holdout_end="2026-04-16T00:00:00Z",
        backtest_run_id=22,
        evaluation_mae=0.8,
    )
    output_dir = tmp_path / "comparison"

    summary = module.compare_training_runs(
        run_dirs=[run_a, run_b],
        output_dir=output_dir,
    )
    saved_json = json.loads((output_dir / "comparison_summary.json").read_text(encoding="utf-8"))
    saved_md = (output_dir / "comparison_summary.md").read_text(encoding="utf-8")

    assert summary["run_count"] == 2
    assert saved_json["differences"]["parent_checkpoints"] == [
        "pfnet/timesfm-1.0-200m-fin",
        "runs/run-a",
    ]
    assert saved_json["differences"]["dataset_manifest_ids"] == ["bundle-a", "bundle-b"]
    assert saved_json["differences"]["backtest_run_ids"] == [11, 22]
    assert "bundle-a" in saved_md
    assert "bundle-b" in saved_md
    assert "pfnet/timesfm-1.0-200m-fin" in saved_md
    assert "runs/run-a" in saved_md
