---
phase: 03-train-the-model-on-1-minute-crypto-candles
verified: 2026-04-16T15:58:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run the documented manual training wrapper against a real prepared bundle in the supported TimesFM v1 environment"
    expected: "A real run directory is created with checkpoint artifacts, run_manifest.json, environment_snapshot.json, evaluation_summary.json, and backtest_summary.json, and the run uses the explicit parent checkpoint supplied by the operator."
    why_human: "Automated tests lock the wrapper contract but do not execute a full JAX/PAX training run on the host."
  - test: "Generate and inspect a comparison report from two real Phase 3 run bundles"
    expected: "comparison_summary.json and comparison_summary.md clearly show parent checkpoint, prepared-bundle identity, holdout ranges, evaluation metrics, and referenced backtest ids in a way an operator can use without reverse-engineering run folders."
    why_human: "Automated tests verify schema and content presence, but not whether a real operator finds the final report readable enough for the intended manual workflow."
---

# Phase 3: Train the model on 1-minute crypto candles Verification Report

**Phase Goal:** Establish a repeatable manual TimesFM v1 fine-tuning workflow from PostgreSQL-backed 1-minute crypto candles with explicit preparation, checkpoint lineage, and comparison-ready reporting.
**Verified:** 2026-04-16T15:58:00Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | The repo now exposes a manual wrapper that launches training from a prepared PostgreSQL-derived bundle without replacing the legacy training engine. | VERIFIED | `src/train_from_postgres.py` validates the prepared bundle, derives a compatible batch size, writes a deterministic run bundle, and invokes `src/main.py`; `tests/test_training_workflow.py` locks the wrapper command and parent-checkpoint behavior. |
| 2 | Every Phase 3 run records explicit parentage, copied config identity, prepared-bundle identity, environment metadata, and command provenance in one deterministic run directory. | VERIFIED | `src/train_from_postgres.py` writes `run_manifest.json`, copied config, and `environment_snapshot.json`; `src/training_environment.py` remains the shared environment capture helper; `tests/test_training_workflow.py` verifies the saved manifest contract. |
| 3 | Canonical holdout evaluation and holdout backtest outputs now exist as explicit file artifacts instead of relying on the trainer's shuffled eval split. | VERIFIED | `src/evaluate_training_run.py` writes `evaluation_summary.json`; `src/backtest_training_run.py` writes `backtest_summary.json`; the wrapper records these as the canonical Phase 3 comparison inputs; `tests/test_training_workflow.py` verifies both outputs. |
| 4 | Completed Phase 3 runs can be normalized into per-run lineage manifests and compared across runs with machine-readable plus operator-readable outputs. | VERIFIED | `src/training_lineage.py` validates run bundles and writes `lineage_manifest.json`; `src/compare_training_runs.py` emits `comparison_summary.json` and `comparison_summary.md`; `tests/test_training_lineage.py` locks the lineage and comparison contract. |
| 5 | Repository docs and automated checks now describe and protect the manual Phase 3 train-and-compare workflow end to end. | VERIFIED | `README.md` documents the prepared-bundle -> manual training -> comparison path; `tests/test_training_workflow.py`, `tests/test_training_lineage.py`, and `node scripts/precommit-checks.mjs` all pass on the current tree. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/train_from_postgres.py` | Manual wrapper for prepared bundles | VERIFIED | Requires explicit parent checkpoint input, derives compatible batch size, writes deterministic run metadata, and delegates to `src/main.py`. |
| `src/evaluate_training_run.py` | Explicit holdout evaluation adapter | VERIFIED | Reads `holdout_series.csv`, evaluates sliding windows, and writes `evaluation_summary.json`. |
| `src/backtest_training_run.py` | Explicit holdout backtest adapter | VERIFIED | Reuses Phase 2 step-metric semantics and writes `backtest_summary.json` with supplemental `backtest_run_id` provenance. |
| `src/main.py` | Legacy trainer entrypoint that accepts explicit parent checkpoint identity | VERIFIED | Accepts `--checkpoint_path` or `--checkpoint_repo_id` from the wrapper. |
| `src/training_lineage.py` | Per-run lineage normalizer | VERIFIED | Validates real evaluation/backtest artifacts and writes `lineage_manifest.json`. |
| `src/compare_training_runs.py` | Cross-run comparison/reporting CLI | VERIFIED | Emits JSON and Markdown comparison outputs and can optionally resolve PostgreSQL backtest metadata. |
| `tests/test_training_workflow.py` | Manual workflow contract coverage | VERIFIED | Covers explicit parent selection, batch-size derivation, deterministic run layout, and post-train summary artifacts. |
| `tests/test_training_lineage.py` | Lineage and comparison contract coverage | VERIFIED | Covers rejection of incomplete bundles and cross-run comparison output differences. |
| `README.md` | Operator docs for manual Phase 3 reporting | VERIFIED | Documents bundle preparation, manual training wrapper usage, and the comparison CLI. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/train_from_postgres.py` | `src/main.py` | wrapper subprocess call | WIRED | The wrapper builds the legacy trainer command and passes explicit parent checkpoint flags into `src/main.py`. |
| `src/train_from_postgres.py` | `src/training_environment.py` | `capture_training_environment()` | WIRED | The wrapper captures one shared environment snapshot before training. |
| `src/train_from_postgres.py` | `src/evaluate_training_run.py` | `evaluate_training_run()` | WIRED | Completed runs always write `evaluation_summary.json` from the explicit holdout artifact. |
| `src/train_from_postgres.py` | `src/backtest_training_run.py` | `backtest_training_run()` | WIRED | Completed runs always write `backtest_summary.json` from the explicit holdout artifact. |
| `src/training_lineage.py` | run bundle artifacts | `run_manifest.json` + summary JSON files | WIRED | Lineage generation refuses incomplete or metadata-only bundles. |
| `src/compare_training_runs.py` | `src/training_lineage.py` | `write_lineage_manifest()` | WIRED | Comparison output is built from normalized run-bundle lineage data. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Workflow and lineage contract suites pass | `.\.venv\Scripts\python.exe -m pytest -q tests/test_training_workflow.py tests/test_training_lineage.py -x` | `11 passed in 0.63s` | PASS |
| Full repo validation stays green on the current tree | `node scripts/precommit-checks.mjs` | `99 passed` and pre-commit gate succeeded | PASS |
| Wrapper test suite remains collection-safe | `.\.venv\Scripts\python.exe -m pytest --collect-only -q tests/test_training_workflow.py` | Contract suite collects cleanly before runtime execution | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `MODEL-01` | `03-01` through `03-05` | User can drive a reproducible training/evaluation workflow from PostgreSQL-derived datasets instead of ad hoc file inputs. | SATISFIED IN CODE | Prepared bundles, wrapper runs, explicit holdout summaries, and comparison reports are all wired and covered by tests. |
| `MODEL-02` | `03-02`, `03-04` | User can materialize model-ready training datasets from the PostgreSQL store with consistent selection rules. | SATISFIED IN CODE | The manifest-driven preparer and the wrapper's prepared-bundle contract are in place and tested. |
| `OPS-01` | `03-03`, `03-04`, `03-05` | User can preserve enough operational metadata to rerun and compare manual training workflows safely, even though scheduled refresh remains deferred. | SATISFIED FOR PHASE GOAL | The phase goal's manual reproducibility path is satisfied in code, but the broader scheduling wording in `.planning/REQUIREMENTS.md` still needs a later dedicated phase. |

### Human Verification Required

### 1. Real Manual Training Run

**Test:** In the supported Linux/WSL/Docker TimesFM v1 environment, prepare a real bundle and run `python src/train_from_postgres.py --bundle-dir <bundle> --output-root <dir> --parent-checkpoint <repo-or-path>`.
**Expected:** The run directory contains checkpoint artifacts plus `run_manifest.json`, `environment_snapshot.json`, `evaluation_summary.json`, and `backtest_summary.json`, and the manifest records the explicit parent checkpoint supplied for the run.
**Why human:** Automated tests do not execute a full JAX/PAX fine-tune on this host.

### 2. Real Comparison Report Readability

**Test:** Produce two real run bundles and run `python src/compare_training_runs.py --run-dir <run-a> --run-dir <run-b> --output-dir <comparison-dir>`.
**Expected:** The generated JSON and Markdown reports make dataset, holdout, parent-checkpoint, evaluation, and backtest provenance differences easy to inspect without hand-auditing the run folders.
**Why human:** Automated checks validate contract structure but not real operator readability.

### Gaps Summary

No blocking code gaps remain in the Phase 03 implementation. The remaining work is manual validation in a real supported training environment and operator sign-off on the readability of the final comparison report.

---

_Verified: 2026-04-16T15:58:00Z_
_Verifier: Codex (inline verification)_
