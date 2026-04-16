from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtest_training_run import backtest_training_run
from evaluate_training_run import evaluate_training_run
from training_environment import (
    capture_training_environment,
    file_sha256,
    write_environment_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIRNAME = "runs"
DEFAULT_TRAIN_RATIO = 0.75


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the legacy TimesFM trainer from a prepared PostgreSQL bundle "
            "and write a deterministic Phase 3 run bundle."
        )
    )
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Prepared bundle directory.")
    parser.add_argument("--output-root", type=Path, required=True, help="Root directory for run bundles.")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "fine_tuning.py",
        help="Training config file to copy into the run bundle.",
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=REPO_ROOT / "requirements.training.txt",
        help="Frozen requirements file used for environment capture.",
    )
    parser.add_argument(
        "--parent-checkpoint",
        required=True,
        help="Explicit parent checkpoint path or Hugging Face repo id.",
    )
    parser.add_argument("--run-name", default=None, help="Optional deterministic run directory name.")
    parser.add_argument(
        "--requested-batch-size",
        type=int,
        default=None,
        help="Override the config batch size before compatibility adjustment.",
    )
    parser.add_argument(
        "--backend",
        default="gpu",
        choices=["cpu", "gpu", "tpu"],
        help="Backend passed through to the legacy TimesFM trainer.",
    )
    parser.add_argument(
        "--python",
        dest="python_executable",
        default=sys.executable,
        help="Python executable used for the legacy trainer subprocess.",
    )
    parser.add_argument(
        "--context-len",
        type=int,
        default=512,
        help="Context length for the post-train holdout evaluation/backtest adapters.",
    )
    parser.add_argument(
        "--horizon-len",
        type=int,
        default=128,
        help="Horizon length for the post-train holdout evaluation/backtest adapters.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=128,
        help="Stride used by the post-train holdout evaluation/backtest adapters.",
    )
    return parser.parse_args(argv)


def utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_prepared_bundle(bundle_dir: Path) -> dict[str, Any]:
    dataset_manifest_path = bundle_dir / "dataset_manifest.json"
    train_windows_path = bundle_dir / "train_windows.csv"
    holdout_series_path = bundle_dir / "holdout_series.csv"
    quality_report_path = bundle_dir / "quality_report.json"

    required_paths = (
        dataset_manifest_path,
        train_windows_path,
        holdout_series_path,
        quality_report_path,
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise ValueError(
            "Prepared bundle is missing required artifacts: " + ", ".join(missing)
        )

    dataset_manifest = read_json(dataset_manifest_path)
    sample_counts = dataset_manifest.get("sample_counts", {})
    total_samples = int(sample_counts.get("total", 0))
    if total_samples <= 0:
        raise ValueError("Prepared bundle sample_counts.total must be a positive integer.")

    return {
        "bundle_dir": bundle_dir.resolve(),
        "dataset_manifest_path": dataset_manifest_path.resolve(),
        "dataset_manifest": dataset_manifest,
        "dataset_manifest_id": dataset_manifest.get("manifest_id"),
        "train_windows_path": train_windows_path.resolve(),
        "holdout_series_path": holdout_series_path.resolve(),
        "quality_report_path": quality_report_path.resolve(),
        "sample_count": total_samples,
    }


def classify_parent_checkpoint(parent_checkpoint: str | None) -> dict[str, str]:
    if not parent_checkpoint:
        raise ValueError("The manual workflow requires an explicit parent checkpoint.")

    candidate = Path(parent_checkpoint)
    if candidate.exists():
        return {"kind": "path", "value": str(candidate.resolve())}
    return {"kind": "repo", "value": parent_checkpoint}


def extract_config_batch_size(config_text: str) -> int:
    match = re.search(r"config\.batch_size\s*=\s*([0-9_ *()+-]+)", config_text)
    if match is None:
        raise ValueError("Could not find config.batch_size in the training config.")
    return int(eval(match.group(1), {"__builtins__": {}}, {}))


def derive_compatible_batch_size(
    *,
    sample_count: int,
    requested_batch_size: int,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
) -> int:
    if sample_count <= 0:
        raise ValueError("Prepared bundle sample count must be positive.")

    train_samples = int(sample_count * train_ratio)
    if train_samples <= 0:
        raise ValueError(
            "Prepared bundle sample count is too small for the trainer's train/eval split."
        )

    candidate = min(requested_batch_size, train_samples)
    while candidate > 0:
        if train_samples % candidate == 0:
            return candidate
        candidate -= 1

    raise ValueError("Unable to derive a compatible batch size from the prepared bundle.")


def copy_config_with_batch_size(
    *,
    source_path: Path,
    destination_path: Path,
    batch_size: int,
) -> None:
    source_text = source_path.read_text(encoding="utf-8")
    updated_text, count = re.subn(
        r"config\.batch_size\s*=\s*([0-9_ *()+-]+)",
        f"config.batch_size = {batch_size}",
        source_text,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not rewrite config.batch_size in the copied training config.")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(updated_text, encoding="utf-8")


def sanitize_run_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not sanitized:
        raise ValueError("Run name must contain at least one filesystem-safe character.")
    return sanitized


def resolve_run_name(run_name: str | None, bundle_manifest_id: str | None) -> str:
    if run_name:
        return sanitize_run_name(run_name)
    suffix = bundle_manifest_id or "bundle"
    return f"{utc_timestamp_slug()}-{suffix}"


def build_training_command(
    *,
    python_executable: str,
    run_dir: Path,
    config_path: Path,
    dataset_path: Path,
    parent_checkpoint: dict[str, str],
    backend: str,
) -> list[str]:
    command = [
        python_executable,
        "src/main.py",
        f"--workdir={run_dir}",
        f"--config={config_path}",
        f"--dataset_path={dataset_path}",
        f"--backend={backend}",
    ]
    if parent_checkpoint["kind"] == "path":
        command.append(f"--checkpoint_path={parent_checkpoint['value']}")
    else:
        command.append(f"--checkpoint_repo_id={parent_checkpoint['value']}")
    return command


def invoke_training_entrypoint(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def run_training_from_bundle(
    *,
    bundle_dir: Path,
    output_root: Path,
    config_path: Path,
    requirements_path: Path,
    parent_checkpoint: str | None,
    run_name: str | None = None,
    requested_batch_size: int | None = None,
    backend: str = "gpu",
    python_executable: str = sys.executable,
    context_len: int = 512,
    horizon_len: int = 128,
    stride: int = 128,
) -> dict[str, Any]:
    bundle = load_prepared_bundle(bundle_dir)
    parent = classify_parent_checkpoint(parent_checkpoint)
    original_config_text = config_path.read_text(encoding="utf-8")
    source_batch_size = extract_config_batch_size(original_config_text)
    effective_batch_size = derive_compatible_batch_size(
        sample_count=bundle["sample_count"],
        requested_batch_size=requested_batch_size or source_batch_size,
    )

    runs_root = output_root / DEFAULT_RUNS_DIRNAME
    run_dir = runs_root / resolve_run_name(run_name, bundle["dataset_manifest_id"])
    run_dir.mkdir(parents=True, exist_ok=True)

    copied_config_path = run_dir / "inputs" / "fine_tuning.py"
    environment_snapshot_path = run_dir / "environment_snapshot.json"
    evaluation_summary_path = run_dir / "evaluation_summary.json"
    backtest_summary_path = run_dir / "backtest_summary.json"
    run_manifest_path = run_dir / "run_manifest.json"

    copy_config_with_batch_size(
        source_path=config_path,
        destination_path=copied_config_path,
        batch_size=effective_batch_size,
    )

    training_command = build_training_command(
        python_executable=python_executable,
        run_dir=run_dir,
        config_path=copied_config_path,
        dataset_path=bundle["train_windows_path"],
        parent_checkpoint=parent,
        backend=backend,
    )
    environment_snapshot = capture_training_environment(
        requirements_path=requirements_path,
        config_path=copied_config_path,
        bundle_manifest_path=bundle["dataset_manifest_path"],
        python_executable=python_executable,
        command=training_command,
    )
    write_environment_snapshot(environment_snapshot, environment_snapshot_path)

    manifest: dict[str, Any] = {
        "phase": "03",
        "status": "running",
        "manual_only": True,
        "run_name": run_dir.name,
        "run_dir": str(run_dir.resolve()),
        "produced_checkpoint": {
            "kind": "local_path",
            "value": str(run_dir.resolve()),
        },
        "parent_checkpoint": parent,
        "prepared_bundle": {
            "bundle_dir": str(bundle["bundle_dir"]),
            "dataset_manifest_path": str(bundle["dataset_manifest_path"]),
            "dataset_manifest_id": bundle["dataset_manifest_id"],
            "train_windows_path": str(bundle["train_windows_path"]),
            "holdout_series_path": str(bundle["holdout_series_path"]),
            "quality_report_path": str(bundle["quality_report_path"]),
            "sample_counts": bundle["dataset_manifest"]["sample_counts"],
            "symbols": bundle["dataset_manifest"]["symbols"],
            "cleaning": bundle["dataset_manifest"]["cleaning"],
            "window_length": bundle["dataset_manifest"]["window_length"],
            "stride": bundle["dataset_manifest"]["stride"],
        },
        "training_config": {
            "source_path": str(config_path.resolve()),
            "copied_path": str(copied_config_path.resolve()),
            "source_sha256": file_sha256(config_path.resolve()),
            "copied_sha256": file_sha256(copied_config_path.resolve()),
            "requested_batch_size": requested_batch_size or source_batch_size,
            "effective_batch_size": effective_batch_size,
        },
        "environment": {
            "snapshot_path": str(environment_snapshot_path.resolve()),
        },
        "training_command": training_command,
        "trainer_internal_eval": {
            "canonical_for_phase3_comparison": False,
            "reason": (
                "The legacy trainer shuffle-eval is not the explicit Phase 3 holdout. "
                "Use evaluation_summary.json and backtest_summary.json for comparisons."
            ),
        },
    }
    write_json(run_manifest_path, manifest)

    invoke_training_entrypoint(training_command)

    evaluation_summary = evaluate_training_run(
        holdout_series_path=bundle["holdout_series_path"],
        output_path=evaluation_summary_path,
        checkpoint_reference=str(run_dir.resolve()),
        checkpoint_kind="path",
        context_len=context_len,
        horizon_len=horizon_len,
        stride=stride,
        backend=backend,
    )
    backtest_summary = backtest_training_run(
        holdout_series_path=bundle["holdout_series_path"],
        output_path=backtest_summary_path,
        checkpoint_reference=str(run_dir.resolve()),
        checkpoint_kind="path",
        context_len=context_len,
        horizon_len=horizon_len,
        stride=stride,
        backend=backend,
    )

    manifest["status"] = "completed"
    manifest["evaluation_summary_path"] = str(evaluation_summary_path.resolve())
    manifest["backtest_summary_path"] = str(backtest_summary_path.resolve())
    manifest["canonical_phase3_outputs"] = [
        str(evaluation_summary_path.resolve()),
        str(backtest_summary_path.resolve()),
    ]
    manifest["backtest_run_id"] = backtest_summary.get("backtest_run_id")
    manifest["evaluation_summary"] = {
        "window_count": evaluation_summary.get("window_count"),
        "point_count": evaluation_summary.get("point_count"),
    }
    manifest["backtest_summary"] = {
        "window_count": backtest_summary.get("window_count"),
        "symbol_count": backtest_summary.get("symbol_count"),
    }
    write_json(run_manifest_path, manifest)
    return manifest


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    manifest = run_training_from_bundle(
        bundle_dir=args.bundle_dir,
        output_root=args.output_root,
        config_path=args.config,
        requirements_path=args.requirements,
        parent_checkpoint=args.parent_checkpoint,
        run_name=args.run_name,
        requested_batch_size=args.requested_batch_size,
        backend=args.backend,
        python_executable=args.python_executable,
        context_len=args.context_len,
        horizon_len=args.horizon_len,
        stride=args.stride,
    )
    print(f"Run bundle: {manifest['run_dir']}")
    print(f"Evaluation summary: {manifest['evaluation_summary_path']}")
    print(f"Backtest summary: {manifest['backtest_summary_path']}")


if __name__ == "__main__":
    main()
