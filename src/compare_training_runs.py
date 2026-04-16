from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from postgres_backtest import query_backtest_step_stats
from postgres_dataset import connect_postgres, load_postgres_settings
from training_lineage import write_lineage_manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two or more Phase 3 training run bundles and write machine-readable "
            "plus operator-readable summaries."
        )
    )
    parser.add_argument(
        "--run-dir",
        dest="run_dirs",
        action="append",
        type=Path,
        required=True,
        help="Run bundle directory. Pass --run-dir multiple times.",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for comparison outputs.")
    parser.add_argument(
        "--resolve-postgres",
        action="store_true",
        help="Resolve referenced backtest_run_id values against PostgreSQL step stats.",
    )
    return parser.parse_args(argv)


def resolve_backtest_metadata(run_id: int | None) -> dict[str, Any] | None:
    if run_id is None:
        return None

    settings = load_postgres_settings()
    with connect_postgres(settings=settings, autocommit=True) as conn:
        step_stats = query_backtest_step_stats(conn=conn, run_id=run_id)
    return {
        "run_id": run_id,
        "step_stats": step_stats,
    }


def summarize_differences(lineages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dataset_manifest_ids": [lineage["dataset_manifest_id"] for lineage in lineages],
        "parent_checkpoints": [
            lineage["parent_checkpoint"]["value"]
            for lineage in lineages
        ],
        "backtest_run_ids": [lineage.get("backtest_run_id") for lineage in lineages],
        "evaluation_mae": [
            lineage["evaluation_summary"]["overall_metrics"]["mae"]
            for lineage in lineages
        ],
        "holdout_ranges": {
            lineage["run_name"]: lineage["per_symbol_ranges"]
            for lineage in lineages
        },
    }


def render_comparison_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Phase 3 Training Run Comparison",
        "",
        f"Runs compared: {summary['run_count']}",
        "",
        "| Run | Parent checkpoint | Dataset manifest | Backtest run id | Eval MAE |",
        "|-----|-------------------|------------------|-----------------|----------|",
    ]
    for run in summary["runs"]:
        lines.append(
            "| "
            f"{run['run_name']} | "
            f"{run['parent_checkpoint']['value']} | "
            f"{run['dataset_manifest_id']} | "
            f"{run.get('backtest_run_id')} | "
            f"{run['evaluation_summary']['overall_metrics']['mae']} |"
        )

    lines.extend(
        [
            "",
            "## Holdout Ranges",
            "",
        ]
    )
    for run in summary["runs"]:
        lines.append(f"### {run['run_name']}")
        for symbol, ranges in run["per_symbol_ranges"].items():
            lines.append(
                f"- {symbol}: train {ranges['train_start_utc']} -> {ranges['train_end_utc']}, "
                f"holdout {ranges['holdout_start_utc']} -> {ranges['holdout_end_utc']}"
            )
    lines.append("")
    return "\n".join(lines)


def compare_training_runs(
    *,
    run_dirs: list[Path],
    output_dir: Path,
    resolve_postgres: bool = False,
) -> dict[str, Any]:
    if len(run_dirs) < 2:
        raise ValueError("Compare at least two run directories.")

    lineages = [write_lineage_manifest(run_dir) for run_dir in run_dirs]
    if resolve_postgres:
        for lineage in lineages:
            lineage["resolved_backtest_metadata"] = resolve_backtest_metadata(
                lineage.get("backtest_run_id")
            )

    summary = {
        "run_count": len(lineages),
        "runs": lineages,
        "differences": summarize_differences(lineages),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "comparison_summary.md").write_text(
        render_comparison_markdown(summary) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = compare_training_runs(
        run_dirs=args.run_dirs,
        output_dir=args.output_dir,
        resolve_postgres=args.resolve_postgres,
    )
    print(f"Saved comparison summary to: {args.output_dir}")
    print(f"Runs compared: {summary['run_count']}")


if __name__ == "__main__":
    main()
