from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


pytestmark = pytest.mark.contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_environment_module():
    return pytest.importorskip("training_environment")


def load_training_workflow_module():
    return pytest.importorskip("train_from_postgres")


def load_evaluation_adapter_module():
    return pytest.importorskip("evaluate_training_run")


def load_backtest_adapter_module():
    return pytest.importorskip("backtest_training_run")


def create_prepared_bundle(
    tmp_path: Path,
    *,
    total_samples: int = 5,
    window_length: int = 640,
    stride: int = 128,
) -> Path:
    bundle_dir = tmp_path / "prepared_bundle"
    bundle_dir.mkdir()
    (bundle_dir / "train_windows.csv").write_text(
        "btc_0001,eth_0001,sol_0001\n"
        "1,2,3\n"
        "4,5,6\n",
        encoding="utf-8",
    )
    (bundle_dir / "holdout_series.csv").write_text(
        "symbol,observation_time_utc,close_price\n"
        "BTCUSDT,2026-01-01T00:00:00Z,70000\n"
        "BTCUSDT,2026-01-01T00:01:00Z,70001\n"
        "BTCUSDT,2026-01-01T00:02:00Z,70002\n"
        "BTCUSDT,2026-01-01T00:03:00Z,70003\n"
        "BTCUSDT,2026-01-01T00:04:00Z,70004\n"
        "BTCUSDT,2026-01-01T00:05:00Z,70005\n",
        encoding="utf-8",
    )
    (bundle_dir / "quality_report.json").write_text(
        json.dumps({"cleaning_mode": "strict", "repairs": []}),
        encoding="utf-8",
    )
    (bundle_dir / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "manifest_id": "bundle-123",
                "source_name": "binance",
                "timeframe": "1m",
                "window_length": window_length,
                "stride": stride,
                "cleaning": {"mode": "strict", "repairable_gap_minutes": 5},
                "sample_counts": {
                    "total": total_samples,
                    "per_symbol": {
                        "BTCUSDT": max(total_samples - 2, 1),
                        "ETHUSDT": 1,
                        "SOLUSDT": 1,
                    },
                },
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "train_start_utc": "2025-11-17T00:00:00Z",
                        "train_end_utc": "2025-12-17T00:00:00Z",
                        "holdout_start_utc": "2025-12-17T00:00:00Z",
                        "holdout_end_utc": "2026-04-16T00:00:00Z",
                    },
                    {
                        "symbol": "ETHUSDT",
                        "train_start_utc": "2025-12-10T00:00:00Z",
                        "train_end_utc": "2026-04-09T00:00:00Z",
                        "holdout_start_utc": "2026-04-09T00:00:00Z",
                        "holdout_end_utc": "2026-04-16T00:00:00Z",
                    },
                    {
                        "symbol": "SOLUSDT",
                        "train_start_utc": "2025-12-10T00:00:00Z",
                        "train_end_utc": "2026-04-09T00:00:00Z",
                        "holdout_start_utc": "2026-04-09T00:00:00Z",
                        "holdout_end_utc": "2026-04-16T00:00:00Z",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return bundle_dir


def test_training_environment_capture_records_python_packages_git_config_and_bundle_identity(
    monkeypatch,
    tmp_path,
) -> None:
    module = load_environment_module()
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\njax==0.4.26\n", encoding="utf-8")
    bundle_manifest_path = tmp_path / "dataset_manifest.json"
    bundle_manifest_path.write_text(
        json.dumps({"manifest_id": "bundle-123"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "capture_pip_freeze",
        lambda python_executable=None: ["timesfm==1.3.0", "jax==0.4.26"],
    )
    monkeypatch.setattr(module, "resolve_git_commit", lambda repo_root=None: "abc1234")

    snapshot = module.capture_training_environment(
        requirements_path=requirements_path,
        config_path=Path("configs/fine_tuning.py"),
        bundle_manifest_path=bundle_manifest_path,
        command=["python", "src/main.py"],
    )

    assert snapshot["manual_only"] is True
    assert snapshot["git_commit"] == "abc1234"
    assert snapshot["config_path"] == "configs/fine_tuning.py"
    assert snapshot["bundle_manifest_id"] == "bundle-123"
    assert snapshot["package_snapshot"] == ["timesfm==1.3.0", "jax==0.4.26"]
    assert snapshot["requirements_file"].endswith("requirements.training.txt")


def test_requirements_training_file_freezes_supported_manual_stack() -> None:
    load_environment_module()
    requirements_path = REPO_ROOT / "requirements.training.txt"
    if not requirements_path.exists():
        pytest.skip("03-03 requirements training freeze has not been implemented yet.")

    lines = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert "timesfm[pax]==1.3.0" in lines
    assert any(line.startswith("jax==") for line in lines)
    assert any(line.startswith("jaxlib==") for line in lines)
    assert any(line.startswith("paxml==") for line in lines)
    assert any(line.startswith("tensorflow") for line in lines)


def test_environment_snapshot_can_point_back_to_requirements_file(tmp_path) -> None:
    module = load_environment_module()
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")

    snapshot = module.capture_training_environment(
        requirements_path=requirements_path,
        config_path=Path("configs/fine_tuning.py"),
        bundle_manifest_path=None,
        packages=["timesfm==1.3.0"],
        git_commit="deadbeef",
    )
    output_path = tmp_path / "environment_snapshot.json"
    module.write_environment_snapshot(snapshot, output_path)

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert saved["requirements_file"] == str(requirements_path)
    assert saved["manual_only"] is True


def test_training_wrapper_rejects_missing_parent_checkpoint(tmp_path) -> None:
    module = load_training_workflow_module()
    bundle_dir = create_prepared_bundle(tmp_path)
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="parent checkpoint"):
        module.run_training_from_bundle(
            bundle_dir=bundle_dir,
            output_root=tmp_path / "outputs",
            config_path=REPO_ROOT / "configs" / "fine_tuning.py",
            requirements_path=requirements_path,
            parent_checkpoint=None,
        )


def test_training_wrapper_records_parentage_batch_size_and_post_train_artifacts(
    monkeypatch,
    tmp_path,
) -> None:
    module = load_training_workflow_module()
    bundle_dir = create_prepared_bundle(tmp_path, total_samples=5, window_length=517, stride=1)
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")
    commands: list[list[str]] = []

    monkeypatch.setattr(module, "utc_timestamp_slug", lambda: "20260416T150000Z")
    monkeypatch.setattr(
        module,
        "capture_training_environment",
        lambda **kwargs: {
            "manual_only": True,
            "bundle_manifest_id": "bundle-123",
            "command": list(kwargs["command"]),
        },
    )

    def fake_train(command: list[str]) -> None:
        commands.append(command)
        workdir_arg = next(item for item in command if item.startswith("--workdir="))
        run_dir = Path(workdir_arg.split("=", 1)[1])
        checkpoint_dir = run_dir / "checkpoints" / "fine-tuning-test"
        (checkpoint_dir / "checkpoint_1").mkdir(parents=True, exist_ok=True)

    def fake_evaluate(**kwargs):
        summary = {
            "checkpoint_reference": kwargs["checkpoint_reference"],
            "canonical_for_phase3_comparison": True,
            "window_count": 2,
        }
        kwargs["output_path"].write_text(json.dumps(summary), encoding="utf-8")
        return summary

    def fake_backtest(**kwargs):
        summary = {
            "checkpoint_reference": kwargs["checkpoint_reference"],
            "canonical_for_phase3_comparison": True,
            "backtest_run_id": 17,
            "supplemental_provenance_only": True,
        }
        kwargs["output_path"].write_text(json.dumps(summary), encoding="utf-8")
        return summary

    monkeypatch.setattr(module, "invoke_training_entrypoint", fake_train)
    monkeypatch.setattr(module, "evaluate_training_run", fake_evaluate)
    monkeypatch.setattr(module, "backtest_training_run", fake_backtest)

    result = module.run_training_from_bundle(
        bundle_dir=bundle_dir,
        output_root=tmp_path / "outputs",
        config_path=REPO_ROOT / "configs" / "fine_tuning.py",
        requirements_path=requirements_path,
        parent_checkpoint="pfnet/timesfm-1.0-200m-fin",
        run_name="starter-run",
        training_output_len=5,
        training_horizon_len=5,
        context_len=None,
        horizon_len=None,
        stride=None,
    )

    run_dir = Path(result["run_dir"])
    copied_config_path = run_dir / "inputs" / "fine_tuning.py"
    manifest_path = run_dir / "run_manifest.json"
    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert run_dir.name == "starter-run"
    assert copied_config_path.exists()
    assert "config.batch_size = 3" in copied_config_path.read_text(encoding="utf-8")
    assert "config.output_len = 5" in copied_config_path.read_text(encoding="utf-8")
    assert "config.horizon_len = 5" in copied_config_path.read_text(encoding="utf-8")
    assert saved_manifest["parent_checkpoint"]["kind"] == "repo"
    assert saved_manifest["parent_checkpoint"]["value"] == "pfnet/timesfm-1.0-200m-fin"
    assert saved_manifest["training_config"]["effective_batch_size"] == 3
    assert saved_manifest["training_config"]["effective_training_shape"]["output_len"] == 5
    assert saved_manifest["training_config"]["effective_training_shape"]["horizon_len"] == 5
    assert saved_manifest["post_train_evaluation"]["horizon_len"] == 5
    assert saved_manifest["post_train_evaluation"]["stride"] == 5
    assert saved_manifest["prepared_bundle"]["dataset_manifest_id"] == "bundle-123"
    assert saved_manifest["trainer_internal_eval"]["canonical_for_phase3_comparison"] is False
    assert saved_manifest["produced_checkpoint"]["value"].endswith("fine-tuning-test")
    assert saved_manifest["backtest_run_id"] == 17
    assert Path(saved_manifest["environment"]["snapshot_path"]).exists()
    assert Path(saved_manifest["evaluation_summary_path"]).exists()
    assert Path(saved_manifest["backtest_summary_path"]).exists()
    assert commands
    assert any("--checkpoint_repo_id=pfnet/timesfm-1.0-200m-fin" == item for item in commands[0])


def test_training_wrapper_uses_checkpoint_path_flag_for_local_parent_checkpoint(
    monkeypatch,
    tmp_path,
) -> None:
    module = load_training_workflow_module()
    bundle_dir = create_prepared_bundle(tmp_path, total_samples=8)
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")
    local_checkpoint = tmp_path / "checkpoint"
    local_checkpoint.mkdir()
    commands: list[list[str]] = []

    monkeypatch.setattr(module, "capture_training_environment", lambda **kwargs: {"command": kwargs["command"]})

    def fake_train(command: list[str]) -> None:
        commands.append(command)
        workdir_arg = next(item for item in command if item.startswith("--workdir="))
        run_dir = Path(workdir_arg.split("=", 1)[1])
        checkpoint_dir = run_dir / "checkpoints" / "fine-tuning-test"
        (checkpoint_dir / "checkpoint_1").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(module, "invoke_training_entrypoint", fake_train)

    def fake_eval(**kwargs):
        summary = {}
        kwargs["output_path"].write_text(json.dumps(summary), encoding="utf-8")
        return summary

    def fake_backtest(**kwargs):
        summary = {"backtest_run_id": None}
        kwargs["output_path"].write_text(json.dumps(summary), encoding="utf-8")
        return summary

    monkeypatch.setattr(module, "evaluate_training_run", fake_eval)
    monkeypatch.setattr(module, "backtest_training_run", fake_backtest)

    module.run_training_from_bundle(
        bundle_dir=bundle_dir,
        output_root=tmp_path / "outputs",
        config_path=REPO_ROOT / "configs" / "fine_tuning.py",
        requirements_path=requirements_path,
        parent_checkpoint=str(local_checkpoint),
        run_name="local-parent",
    )

    assert commands
    assert any(f"--checkpoint_path={local_checkpoint}" == item for item in commands[0])
    assert not any(item.startswith("--checkpoint_repo_id=") for item in commands[0])


def test_training_wrapper_rejects_incompatible_output_and_horizon_lengths(tmp_path) -> None:
    module = load_training_workflow_module()
    bundle_dir = create_prepared_bundle(tmp_path, total_samples=8)
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="output_len and horizon_len"):
        module.run_training_from_bundle(
            bundle_dir=bundle_dir,
            output_root=tmp_path / "outputs",
            config_path=REPO_ROOT / "configs" / "fine_tuning.py",
            requirements_path=requirements_path,
            parent_checkpoint="pfnet/timesfm-1.0-200m-fin",
            training_output_len=8,
            training_horizon_len=5,
        )


def test_training_wrapper_rejects_bundle_window_length_mismatch(tmp_path) -> None:
    module = load_training_workflow_module()
    bundle_dir = create_prepared_bundle(tmp_path, total_samples=8, window_length=640)
    requirements_path = tmp_path / "requirements.training.txt"
    requirements_path.write_text("timesfm[pax]==1.3.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="window_length"):
        module.run_training_from_bundle(
            bundle_dir=bundle_dir,
            output_root=tmp_path / "outputs",
            config_path=REPO_ROOT / "configs" / "fine_tuning.py",
            requirements_path=requirements_path,
            parent_checkpoint="pfnet/timesfm-1.0-200m-fin",
            training_output_len=5,
            training_horizon_len=5,
        )


def test_evaluation_adapter_writes_holdout_summary_for_explicit_artifact(tmp_path) -> None:
    module = load_evaluation_adapter_module()
    holdout_path = tmp_path / "holdout_series.csv"
    output_path = tmp_path / "evaluation_summary.json"
    holdout_path.write_text(
        "symbol,observation_time_utc,close_price\n"
        "BTCUSDT,2026-01-01T00:00:00Z,10\n"
        "BTCUSDT,2026-01-01T00:01:00Z,11\n"
        "BTCUSDT,2026-01-01T00:02:00Z,12\n"
        "BTCUSDT,2026-01-01T00:03:00Z,13\n"
        "BTCUSDT,2026-01-01T00:04:00Z,14\n"
        "BTCUSDT,2026-01-01T00:05:00Z,15\n"
        "BTCUSDT,2026-01-01T00:06:00Z,16\n"
        "BTCUSDT,2026-01-01T00:07:00Z,17\n",
        encoding="utf-8",
    )

    def fake_forecast(*, contexts, **_kwargs):
        return np.asarray([[14.0, 15.0], [16.0, 17.0]], dtype=float)

    summary = module.evaluate_training_run(
        holdout_series_path=holdout_path,
        output_path=output_path,
        checkpoint_reference="runs/starter-run",
        checkpoint_kind="path",
        context_len=4,
        horizon_len=2,
        stride=2,
        forecast_contexts=fake_forecast,
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert summary["window_count"] == 2
    assert saved["holdout_series_path"] == str(holdout_path)
    assert saved["canonical_for_phase3_comparison"] is True
    assert saved["overall_metrics"]["mae"] == pytest.approx(0.0)


def test_backtest_adapter_writes_summary_and_supplemental_backtest_run_ids(tmp_path) -> None:
    module = load_backtest_adapter_module()
    holdout_path = tmp_path / "holdout_series.csv"
    output_path = tmp_path / "backtest_summary.json"
    holdout_path.write_text(
        "symbol,observation_time_utc,close_price\n"
        "BTCUSDT,2026-01-01T00:00:00Z,10\n"
        "BTCUSDT,2026-01-01T00:01:00Z,11\n"
        "BTCUSDT,2026-01-01T00:02:00Z,12\n"
        "BTCUSDT,2026-01-01T00:03:00Z,13\n"
        "BTCUSDT,2026-01-01T00:04:00Z,14\n"
        "BTCUSDT,2026-01-01T00:05:00Z,15\n"
        "BTCUSDT,2026-01-01T00:06:00Z,16\n"
        "BTCUSDT,2026-01-01T00:07:00Z,17\n",
        encoding="utf-8",
    )

    def fake_forecast(*, contexts, **_kwargs):
        return np.asarray([[14.0, 15.0], [16.0, 17.0]], dtype=float)

    summary = module.backtest_training_run(
        holdout_series_path=holdout_path,
        output_path=output_path,
        checkpoint_reference="runs/starter-run",
        checkpoint_kind="path",
        context_len=4,
        horizon_len=2,
        stride=2,
        forecast_contexts=fake_forecast,
        persist_symbol_backtest=lambda **kwargs: 17,
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert summary["backtest_run_id"] == 17
    assert saved["supplemental_provenance_only"] is True
    assert saved["backtest_run_ids"]["BTCUSDT"] == 17
    assert saved["symbol_summaries"][0]["step_stats"]
