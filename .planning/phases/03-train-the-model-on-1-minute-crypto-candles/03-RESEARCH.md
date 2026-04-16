# Phase 3: Train the model on 1-minute crypto candles - Research

**Researched:** 2026-04-16  
**Domain:** PostgreSQL-backed crypto-minute dataset preparation, legacy TimesFM v1 fine-tuning workflow, and checkpoint lineage for manual retraining  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Dataset scope and coverage
- **D-01:** Phase 3 stays focused on three Binance spot `1m` pairs only: `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`.
- **D-02:** The target historical coverage is `40` months for `BTCUSDT` and `36` months each for `ETHUSDT` and `SOLUSDT`.
- **D-03:** The extra `4` months on Bitcoin exist specifically so the latest `4` months can remain available for backtests instead of being consumed by default training exports.
- **D-04:** Broader symbol configurability is not required in this phase beyond choosing among the three supported pairs.

### Training window selection
- **D-05:** Fine-tuning inputs must support fully custom `start` and `end` ranges per symbol rather than only fixed rolling windows or one shared calendar slice.
- **D-06:** The workflow should still make common cases easy through presets or simple defaults, but the canonical capability is custom per-symbol date selection.
- **D-07:** The first intended training round is one month of data from each of the three supported pairs.

### Holdout and backtest separation
- **D-08:** Holdout periods must be configurable per symbol rather than hard-coded globally.
- **D-09:** `BTCUSDT` should default to reserving the latest `4` months for backtests.
- **D-10:** `ETHUSDT` and `SOLUSDT` should also use configurable holdout ranges, but this phase does not lock them to the same default as Bitcoin.
- **D-11:** The training/preparation workflow must make the training slice and the reserved holdout slice explicit in outputs and metadata so later comparisons are reproducible.

### Data cleaning and preparation
- **D-12:** Raw minute candles are not acceptable as direct model input; Phase 3 must introduce a dedicated cleaner/preparer step before fine-tuning.
- **D-13:** The preparer must support both strict and repair-capable operation rather than forcing only one cleaning policy.
- **D-14:** The canonical output is a cleaned model-ready dataset plus a quality report that explains what was dropped, repaired, aligned, or rejected.
- **D-15:** Research and planning must determine the exact preparation contract required by the current TimesFM v1 fine-tuning path, including how PostgreSQL-backed minute candles should be transformed into the dataset shape consumed by `src/train.py`.

### Snapshot and experiment tracking
- **D-16:** Every manual fine-tune run must produce snapshotable model artifacts so later runs can be compared against earlier ones.
- **D-17:** The baseline metadata saved per run should include at minimum: produced checkpoint, parent checkpoint, selected symbols, per-symbol training date ranges, per-symbol holdout definition, preparer settings, training config used, and evaluation/backtest summary.
- **D-18:** Snapshot tracking should make it clear how each new training dataset affected later comparisons, rather than treating checkpoints as anonymous files in a work directory.

### Retraining workflow shape
- **D-19:** Phase 3 only needs a reusable manual CLI-driven retraining workflow for repeated runs.
- **D-20:** Scheduled or automatic retraining is explicitly deferred to a later phase.

### the agent's Discretion
- The exact CLI surface for selecting per-symbol date ranges, holdouts, and presets is left to the agent as long as it stays explicit and reproducible.
- The exact cleaning heuristics, repair thresholds, and report layout are left to research and planning, provided the workflow supports both strict and repair-capable modes.
- The exact storage mechanism for snapshot metadata can be file-based, PostgreSQL-backed, or hybrid, as long as lineage and comparison inputs are preserved reliably.

### Deferred Ideas (OUT OF SCOPE)
- Automatic or scheduled retraining is deferred to a later phase.
- Expanding beyond `BTCUSDT`, `ETHUSDT`, and `SOLUSDT` is deferred until this repeatable three-pair workflow is proven.
- Broader model-serving or hosted orchestration remains out of scope; Phase 3 stays a local manual workflow.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODEL-01 | User can drive forecasting or evaluation workflows directly from PostgreSQL-backed datasets instead of ad hoc file inputs. | Phase 3 should keep PostgreSQL as the canonical source of candles and materialize a reproducible training bundle from explicit per-symbol selectors instead of hand-edited CSVs. The existing repo already centralizes PostgreSQL settings/bootstrap in `src/postgres_dataset.py`, and Phase 2 already persists backtest facts in PostgreSQL for later comparison. [VERIFIED: `src/postgres_dataset.py`, `src/postgres_backtest.py`, `03-CONTEXT.md`] |
| MODEL-02 | User can materialize model-ready training or inference datasets from the PostgreSQL store with consistent selection rules. | The current trainer contract is stricter than the existing `training_matrix` export: `src/train.py` expects numeric-only samples, drops NaN-bearing columns, transposes the matrix into example rows, shuffles them, log-transforms them, and uses a 512-input/128-output training shape. Phase 3 therefore needs a dedicated cleaner/preparer that emits fixed-length positive windows plus a manifest and quality report, not just a raw aligned panel. [VERIFIED: `src/train.py`, `src/postgres_materialize_dataset.py`, `configs/fine_tuning.py`] |
| OPS-01 | User can schedule recurring data refreshes into PostgreSQL. | Scheduling is explicitly out of scope, but Phase 3 should preserve manual reproducibility by recording the exact source coverage, holdouts, and ingestion state that each training bundle used, so a later scheduling phase can rerun the same workflow safely against refreshed PostgreSQL data. [VERIFIED: `03-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `src/postgres_ingest_binance.py`] |
</phase_requirements>

## Summary

Phase 3 should not be planned as "add more symbols, export one CSV, run `src/main.py`." The current training path is a legacy TimesFM v1 JAX/PAX workflow whose data contract is narrower than the existing PostgreSQL `training_matrix` bridge: the trainer reads numeric CSV, drops any column containing `NaN`, transposes columns into training examples, shuffles examples randomly, log-transforms values, and assumes a 512-input / 128-output sequence layout. That means the planner needs a new preparation layer that emits fixed-length window samples plus explicit train-vs-holdout metadata. [VERIFIED: `src/train.py`, `src/main.py`, `configs/fine_tuning.py`, `src/postgres_materialize_dataset.py`]

Two code-level risks dominate planning. First, the current `training_matrix` export cannot satisfy Phase 3 by itself: it supports only one common date filter across all series and produces one column per aligned series, which is incompatible with custom per-symbol ranges and holdouts. Second, the trainer's built-in 75/25 random row split cannot represent explicit per-symbol holdout windows and would leak heavily if Phase 3 generates overlapping rolling windows, because adjacent windows from the same calendar segment would be shuffled across both train and eval. [VERIFIED: `src/postgres_materialize_dataset.py`, `src/train.py`, `03-CONTEXT.md`]

The safest architecture is: keep PostgreSQL and Phase 2 backtest tables as the canonical data sources, introduce a manifest-first cleaner/preparer that selects per-symbol ranges and emits fixed-length model windows plus a quality report, run training through a thin wrapper around the existing `src/main.py` path with explicit parent checkpoint and config capture, and save a file-based run bundle that links checkpoints to dataset manifests and Phase 2 backtest run IDs. This stays CLI-first, avoids inventing a service, and gives the planner clear waves: data coverage and quality, preparation contract, training workflow, then lineage/comparison/reporting. [VERIFIED: `03-CONTEXT.md`, `.planning/PROJECT.md`, `src/main.py`, `src/postgres_backtest.py`]

**Primary recommendation:** Plan Phase 3 around a PostgreSQL-to-window-bundle preparer and a manifest-driven training wrapper; do not treat the existing `training_matrix` export or `src/train.py` random split as sufficient. [VERIFIED: `src/train.py`, `src/postgres_materialize_dataset.py`, `03-CONTEXT.md`]

## Current Data Reality

The live PostgreSQL database currently contains only one `1m` Binance series, `BTCUSDT`, with `526,156` stored rows from `2024-01-01T00:00:00Z` through `2026-04-14T22:12:00Z`. `ETHUSDT` and `SOLUSDT` are not present yet, so the Phase 3 plan must include data expansion before any three-symbol training workflow is possible. [VERIFIED: live `docker compose exec postgres psql` query on 2026-04-16]

That stored BTC series is not currently contiguous across the full visible date span: there is one gap of `469 days 12:58:00` between `2024-01-01T00:09:00Z` and `2025-04-14T13:07:00Z`, with `0` duplicate timestamps and `0` non-minute-aligned timestamps. This is direct evidence that Phase 3 needs strict-versus-repair cleaning modes and must never assume "data exists in PostgreSQL" means "safe to train over the whole span." [VERIFIED: live `docker compose exec postgres psql` gap/duplicate/alignment queries on 2026-04-16]

Phase 2 backtest runs are already being persisted in PostgreSQL with run-level metadata such as symbol, context length, horizon, stride, batch size, and stored source coverage. Phase 3 should reuse those `run_id` records in checkpoint comparison manifests instead of inventing a second comparison ledger. [VERIFIED: live `docker compose exec postgres psql` query of `market_data.backtest_runs`, `src/postgres_backtest.py`]

## Standard Stack

### Core

| Library / Component | Version to Use | Purpose | Why Standard |
|---------------------|----------------|---------|--------------|
| PostgreSQL market-data and backtest store | Existing Phase 1/2 schema | Canonical source candles, coverage discovery, holdout definition, and backtest comparison linkage | Phase 1 locked PostgreSQL as the data foundation, and Phase 2 already persists backtest runs there; Phase 3 should extend that path instead of creating a second source of truth. [VERIFIED: `01-CONTEXT.md`, `02-CONTEXT.md`, `src/postgres_dataset.py`, `src/postgres_backtest.py`] |
| `timesfm[pax]==1.3.0` | `1.3.0` (PyPI release uploaded `2025-07-06`) | Legacy TimesFM v1 runtime for fine-tuning and checkpoint loading | The official TimesFM README states that checkpoint families `1.0` and `2.0` are archived under `v1` and should be loaded with `timesfm==1.3.0`; the PyPI package metadata for `1.3.0` exposes the `pax` extra needed for JAX/PAX training on Python 3.10. [CITED: https://github.com/google-research/timesfm/blob/master/README.md] [VERIFIED: https://pypi.org/pypi/timesfm/1.3.0/json] |
| Python `3.10.x` environment | `3.10.11` available locally | Supported runtime for the legacy v1 stack | The repo requires Python 3.10, `timesfm` 1.3.0 declares `>=3.10,<3.12`, and the host already has Python `3.10.11`; Phase 3 should stay on that runtime rather than drifting to newer interpreters. [VERIFIED: local `python --version`, `.planning/PROJECT.md`, https://pypi.org/pypi/timesfm/1.3.0/json] |
| File-based dataset and run manifests | JSON via Python stdlib | Reproducible manual CLI workflow without introducing a service | The repo is CLI-first, Phase 3 is manual-only, and the user requires explicit per-symbol ranges, holdouts, cleaner settings, checkpoint parentage, and evaluation/backtest summaries per run; a manifest bundle satisfies that without adding a hosted control plane. [VERIFIED: `.planning/PROJECT.md`, `03-CONTEXT.md`] |

### Supporting

| Library / Component | Version to Use | Purpose | When to Use |
|---------------------|----------------|---------|-------------|
| `psycopg[binary]==3.3.3` | `3.3.3` (PyPI release uploaded `2026-02-18`) | Shared PostgreSQL access for selector, preparer, and lineage helpers | The repo already pins `psycopg[binary]==3.3.3` and routes PostgreSQL access through `src/postgres_dataset.py`; Phase 3 should reuse that exact path. [VERIFIED: `requirements.inference.txt`, `src/postgres_dataset.py`, https://pypi.org/pypi/psycopg/json] |
| `pandas>=2.2,<3.0` | Keep repo pin, do not upgrade during Phase 3 | Cleaning, alignment, window materialization, and report generation | The repo pins `<3.0`, while current PyPI is `3.0.2`; the planner should avoid opportunistic upgrades and stay on the repo's known range while hardening the workflow. [VERIFIED: `requirements.inference.txt`, https://pypi.org/pypi/pandas/json] |
| `numpy>=1.26,<2.0` | Keep repo pin, do not upgrade during Phase 3 | Numeric window construction and metrics inputs | The repo pins `<2.0`, while current PyPI is `2.4.4`; Phase 3 should preserve the repo's compatibility envelope instead of adding a NumPy migration. [VERIFIED: `requirements.inference.txt`, https://pypi.org/pypi/numpy/json] |
| `pytest==9.0.3` | `9.0.3` | Contract, unit, and integration verification for the new preparation and lineage flow | The repo already pins `pytest==9.0.3` in `requirements.dev.txt` and uses `pytest.ini`; Phase 3 should extend that suite. [VERIFIED: `requirements.dev.txt`, `pytest.ini`] |
| JAX / PaxML / Praxis / TensorFlow from a captured `timesfm[pax]` environment | Capture and freeze a known-good set in Wave 0 | Legacy trainer backend | `timesfm` `1.3.0` requests `jax[cuda12]>=0.4.26`, `jaxlib>=0.4.26`, `paxml>=1.4.0`, and `lingvo>=0.12.7` for the `pax` extra on Python 3.10, while current latest `jax` on PyPI now requires Python `>=3.11`; Phase 3 must capture a reproducible environment instead of installing unconstrained latest packages. [VERIFIED: https://pypi.org/pypi/timesfm/1.3.0/json, https://pypi.org/pypi/jax/json, https://pypi.org/pypi/paxml/json, `src/train.py`, `src/evaluation.py`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Materialized training bundle from PostgreSQL | Direct streaming from PostgreSQL into `src/train.py` | Direct database reads would require a larger trainer refactor for batching, splitting, and reproducible manifests, while the current code already consumes files via `dataset_path`. [VERIFIED: `src/main.py`, `src/train.py`] |
| File-based run bundle with backtest references | New PostgreSQL training-runs tables in Phase 3 | Database-backed training metadata may become useful later, but file bundles are the lowest-risk fit for a manual CLI phase and still allow references back to PostgreSQL `run_id` values. [VERIFIED: `.planning/PROJECT.md`, `03-CONTEXT.md`, `src/postgres_backtest.py`] |

**Installation:**
```bash
python -m pip install -r requirements.inference.txt
python -m pip install -r requirements.dev.txt
python -m pip install "timesfm[pax]==1.3.0"
```

**Version verification:** The recommended stack above was cross-checked against repo pins and current PyPI metadata on 2026-04-16. `timesfm` current version is still `1.3.0`, `psycopg` current version is `3.3.3`, `pytest` is repo-pinned to `9.0.3`, while `pandas` and `numpy` latest releases are newer than the repo's allowed ranges and should not be adopted inside this phase. [VERIFIED: `requirements.inference.txt`, `requirements.dev.txt`, https://pypi.org/pypi/timesfm/json, https://pypi.org/pypi/psycopg/json, https://pypi.org/pypi/pandas/json, https://pypi.org/pypi/numpy/json]

## Architecture Patterns

### Recommended Project Structure
```text
src/
|-- training_dataset_manifest.py   # Parse/validate per-symbol ranges, holdouts, and cleaner settings
|-- postgres_prepare_training.py   # Query PostgreSQL, audit quality, emit fixed-length window bundles
|-- train_from_postgres.py         # Manual CLI wrapper around src/main.py with explicit checkpoint/config capture
`-- compare_training_runs.py       # Summarize eval/backtest links for two or more checkpoint runs
```

### Pattern 1: Manifest-First Dataset Selection

**What:** Use one committed-or-saved JSON manifest as the canonical input for a manual run, with entries for each symbol's training range, holdout range, source/timeframe, cleaning mode, and output window settings. This is the simplest way to satisfy explicit per-symbol date control and reproducibility in a CLI-first repo. [VERIFIED: `.planning/PROJECT.md`, `03-CONTEXT.md`]

**When to use:** Use this for every Phase 3 bundle creation and every retraining run; do not treat repeated CLI flags alone as the reproducibility record. [VERIFIED: `03-CONTEXT.md`]

**Key fields the planner should require:** `symbols[]`, `source_name`, `timeframe`, `train_start_utc`, `train_end_utc`, `holdout_start_utc`, `holdout_end_utc`, `cleaning_mode`, `repair_policy`, `window_length`, `stride`, `parent_checkpoint`, `training_config_path`, and `notes`. These are all either explicitly required by Phase 3 decisions or needed to reconstruct the current trainer input. [VERIFIED: `03-CONTEXT.md`, `src/main.py`, `src/train.py`, `configs/fine_tuning.py`]

### Pattern 2: Fixed-Length Window Bundle, Not Full-History Panel

**What:** Emit a model-ready CSV where each column is one contiguous positive window of exactly `input_len + output_len` points, not one column per full symbol history. With the current defaults, that means `640` rows per sample column (`512` context + `128` target). [VERIFIED: `src/train.py`, `configs/fine_tuning.py`]

**When to use:** Use this for the training bundle that feeds `src/main.py --dataset_path ...`. The existing `training_matrix` export is still useful as a raw alignment bridge, but it is not sufficient as the final Phase 3 contract. [VERIFIED: `src/postgres_materialize_dataset.py`, `src/main.py`, `src/train.py`]

**Why the fixed-length contract matters:** In `train=True`, `prepare_batch_data()` delegates to `random_masking()` without passing config-driven lengths. `random_masking()` always builds `input_padding` at `context_len=512`, while `input_sequences` becomes `sequence_length - output_len`. The shape is coherent only when `sequence_length == 512 + 128`. [VERIFIED: `src/train.py`]

**Required sidecars:** Save `quality_report.json`, `dataset_manifest.json`, `window_index.csv` or equivalent, and a machine-readable summary of how many windows were emitted, dropped, repaired, or rejected by symbol and reason. Phase 3 explicitly requires these outputs. [VERIFIED: `03-CONTEXT.md`]

### Pattern 3: Separate Train and Holdout Bundles

**What:** Materialize training windows and holdout/backtest windows separately, or at minimum store separate manifests that encode those boundaries explicitly. Do not rely on `preprocess_csv()` to infer a valid holdout split. [VERIFIED: `src/train.py`, `03-CONTEXT.md`]

**When to use:** Use this whenever the bundle contains overlapping rolling windows or per-symbol holdout calendars, which is exactly the Phase 3 shape. [VERIFIED: `03-CONTEXT.md`]

**Why:** `preprocess_csv()` transposes, shuffles, and then splits rows randomly by `train_ratio=0.75`. If Phase 3 uses rolling windows, that random split would mix overlapping windows from the same time region across train and eval, invalidating the explicit holdout requirement. [VERIFIED: `src/train.py`]

### Pattern 4: File-First Run Bundle with Phase 2 References

**What:** Save each training run under a deterministic directory such as `workdir/runs/<timestamp-or-slug>/` with the emitted bundle manifest, copied config, checkpoint path, parent checkpoint identifier, training command, trainer logs, evaluation summary, and referenced Phase 2 `backtest_run_id` values. [VERIFIED: `03-CONTEXT.md`, `src/main.py`, `src/train.py`, `src/postgres_backtest.py`]

**When to use:** Use this for every manual fine-tune run and every comparison report. [VERIFIED: `03-CONTEXT.md`]

### Anti-Patterns to Avoid

- **Reuse `training_matrix` as the final Phase 3 contract:** It only supports one shared date filter and one column per aligned series, so it cannot express per-symbol ranges or explicit holdouts. [VERIFIED: `src/postgres_materialize_dataset.py`, `03-CONTEXT.md`]
- **Rely on the trainer's implicit eval split:** The current row shuffle is incompatible with explicit holdout calendars and would create leakage with overlapping rolling windows. [VERIFIED: `src/train.py`]
- **Keep the parent checkpoint implicit:** `src/main.py` defaults to `google/timesfm-1.0-200m` when `--checkpoint_path` is absent, while the repo README presents the finance-tuned checkpoint as the operator-facing default for inference. Phase 3 should record parentage explicitly. [VERIFIED: `src/main.py`, `README.md`, https://huggingface.co/pfnet/timesfm-1.0-200m-fin]
- **Treat all gaps as repairable:** The live BTC series already contains a `469`-day gap, which must be rejected or segmented, not forward-filled. [VERIFIED: live `docker compose exec postgres psql` gap query on 2026-04-16]
- **Float the JAX/PAX dependency set to latest:** Current latest `jax` requires Python `>=3.11`, while this repo is intentionally anchored to Python `3.10` and TimesFM v1. [VERIFIED: `.planning/PROJECT.md`, https://pypi.org/pypi/jax/json, https://pypi.org/pypi/timesfm/1.3.0/json]

## Dataset Contract the Planner Must Honor

1. The current trainer consumes a numeric CSV only; non-numeric date columns are not accepted by `preprocess_csv()`. [VERIFIED: `src/train.py`]
2. Every retained sample column must be complete; any column containing a `NaN` is dropped before training. [VERIFIED: `src/train.py`]
3. Training values must stay strictly positive because `train_and_evaluate()` applies `jnp.log(batch)` before every train and eval step. [VERIFIED: `src/train.py`]
4. The safest Phase 3 sample length for the current code is `640` points per example column, matching `512` input plus `128` output. [VERIFIED: `src/train.py`, `configs/fine_tuning.py`]
5. Train and holdout should be explicit artifacts, not inferred from the trainer's internal random split. [VERIFIED: `src/train.py`, `03-CONTEXT.md`]
6. Window identifiers should preserve `symbol`, `window_start_utc`, `window_end_utc`, and cleaning outcome so later comparison reports can trace every sample back to PostgreSQL coverage. This is needed to satisfy the Phase 3 lineage requirements. [VERIFIED: `03-CONTEXT.md`]

## Concrete Planning Implications

The first intended experiment is one month of `BTCUSDT`, `ETHUSDT`, and `SOLUSDT` minute data. One month is about `43,200` minutes per symbol. If the planner emits rolling windows of `640` points with stride `128`, that produces `333` windows per symbol and `999` total; after the trainer's hard-coded `75%` split and batch-size rounding to the legacy default `1024`, `train_size` becomes `0`, so the current default batch size is unusable for that first run. [VERIFIED: local arithmetic from `43,200` minutes, `640`-point windows, `train_ratio=0.75`, and `config.batch_size=1024`; `src/train.py`, `configs/fine_tuning.py`]

Even if the planner lowers the batch size, overlapping windows plus the current random row split would still create optimistic evaluation leakage. The phase plan therefore needs one of these two outcomes before implementation is considered complete: either separate train/eval materializations that the trainer can consume explicitly, or a wrapper that bypasses the trainer's internal random split for true holdout evaluation and uses Phase 2 backtests or a dedicated eval bundle instead. [VERIFIED: `src/train.py`, `src/evaluation.py`, `03-CONTEXT.md`]

The live database also shows that "enough data" and "clean enough data" are different questions. The planner should treat multi-symbol backfill and quality verification as prerequisites for any training run, not as optional prep, because the current stored BTC span includes a giant hole and the other two required symbols do not exist in PostgreSQL yet. [VERIFIED: live `docker compose exec postgres psql` coverage and gap queries on 2026-04-16]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Canonical source data store | New SQLite/CSV-only training store | Existing PostgreSQL data layer plus explicit materialization bundle | PostgreSQL is already the locked source of truth from Phases 1 and 2, and Phase 3 must build on it. [VERIFIED: `01-CONTEXT.md`, `02-CONTEXT.md`, `03-CONTEXT.md`] |
| Training engine | New bespoke trainer | Existing `src/main.py` + `src/train.py` execution core behind a safer wrapper | The repo already has a functioning legacy trainer; Phase 3's main gap is data contract and reproducibility, not inventing a second fine-tuning stack. [VERIFIED: `src/main.py`, `src/train.py`] |
| Holdout comparison ledger | Ad hoc spreadsheet notes or unnamed checkpoint folders | Run bundle manifests that reference Phase 2 `backtest_run_id` rows | Phase 2 already persists comparable backtest metadata in PostgreSQL; Phase 3 only needs deterministic cross-links. [VERIFIED: `src/postgres_backtest.py`, live `market_data.backtest_runs` query on 2026-04-16] |
| Gap detection and coverage math | Shell scripts or unchecked heuristics | Reuse/extend `src/postgres_verify_data.py`-style integrity checks plus SQL-backed quality reports | The repo already has integrity concepts for duplicates, gaps, ordering, nulls, and coverage; Phase 3 should deepen that path rather than fork it. [VERIFIED: `src/postgres_verify_data.py`] |

**Key insight:** Phase 3 is mostly a contract-hardening phase around PostgreSQL selection, window materialization, and lineage capture. The current trainer is legacy but usable if the planner feeds it the exact sample shape it expects and stops relying on its implicit split behavior. [VERIFIED: `src/train.py`, `src/main.py`, `03-CONTEXT.md`]

## Common Pitfalls

### Pitfall 1: Export one aligned panel and assume the trainer can learn from it

**What goes wrong:** With one column per symbol history, the trainer gets only a handful of examples, not a training corpus, and its batch-size math can collapse to zero useful training rows. [VERIFIED: `src/postgres_materialize_dataset.py`, `src/train.py`, `configs/fine_tuning.py`]

**Why it happens:** The existing PostgreSQL `training_matrix` bridge was built as a generic CSV compatibility layer, not as a true fixed-window sample generator. [VERIFIED: `src/postgres_materialize_dataset.py`]

**How to avoid:** Generate contiguous fixed-length sample windows and make sample count a first-class preparer report item before launching training. [VERIFIED: `src/train.py`, `03-CONTEXT.md`]

**Warning signs:** Very low sample counts, `train_size` rounding to zero, or runs that finish without meaningful training progress. [VERIFIED: `src/train.py`, `configs/fine_tuning.py`]

### Pitfall 2: Treat the trainer's random 75/25 split as the Phase 3 holdout design

**What goes wrong:** Holdout leakage makes eval look better than it really is, especially when adjacent rolling windows overlap. [VERIFIED: `src/train.py`]

**Why it happens:** `preprocess_csv()` shuffles rows and splits them randomly after transpose, with no notion of per-symbol calendars or future holdouts. [VERIFIED: `src/train.py`]

**How to avoid:** Materialize train and holdout explicitly and keep true holdout evaluation outside that random split path. [VERIFIED: `03-CONTEXT.md`, `src/train.py`]

**Warning signs:** Eval windows sharing the same symbol/date region as training windows or difficulty explaining exactly which dates were held out. [VERIFIED: `03-CONTEXT.md`]

### Pitfall 3: Repair long outages instead of segmenting or rejecting them

**What goes wrong:** Forward-filling or interpolating over large missing spans creates synthetic price history and corrupts both training and later comparisons. [VERIFIED: live BTC gap query on 2026-04-16]

**Why it happens:** Minute-candle datasets look dense, so it is easy to assume missing points are always tiny transport glitches. The live database already disproves that assumption. [VERIFIED: live BTC gap query on 2026-04-16]

**How to avoid:** Make strict mode reject any missing-minute gap in the selected range, and make repair mode explicitly cap what counts as a short repairable gap while logging every repair in the quality report. [VERIFIED: `03-CONTEXT.md`, live BTC gap query on 2026-04-16]

**Warning signs:** Large repaired-minute counts, windows spanning multiple gap segments, or training bundles that join distant calendar periods into one continuous sample. [VERIFIED: `03-CONTEXT.md`]

### Pitfall 4: Leave parent checkpoint selection implicit

**What goes wrong:** Later comparisons become ambiguous because the run bundle cannot distinguish "fine-tuned from Google base" from "continued from an earlier finance-tuned checkpoint." [VERIFIED: `src/main.py`, `03-CONTEXT.md`]

**Why it happens:** `src/main.py` silently falls back to `google/timesfm-1.0-200m` when `--checkpoint_path` is absent. [VERIFIED: `src/main.py`]

**How to avoid:** Make the Phase 3 wrapper require an explicit parent checkpoint identifier and store it in the run manifest. [VERIFIED: `03-CONTEXT.md`, `src/main.py`]

**Warning signs:** Checkpoint directories with timestamps only and no copied metadata about parentage or config. [VERIFIED: `src/train.py`, `03-CONTEXT.md`]

## Plan Decomposition Guidance

1. **Wave 0: Freeze the environment and the training contract.** Capture a known-good Python 3.10 + `timesfm[pax]==1.3.0` environment, decide whether the wrapper parent checkpoint default should be the finance-tuned PFN model or an explicit operator choice, and lock the prepared sample shape plus train-vs-holdout artifact contract before writing new runtime code. [VERIFIED: `src/main.py`, `src/train.py`, `README.md`, https://github.com/google-research/timesfm/blob/master/README.md, https://huggingface.co/pfnet/timesfm-1.0-200m-fin]
2. **Wave 1: Expand and verify PostgreSQL source data.** Add ETH/SOL coverage, repair or intentionally segment the BTC history gap, and extend discovery/integrity reporting so a manifest selector can validate each requested symbol/date range before materialization. [VERIFIED: `03-CONTEXT.md`, live PostgreSQL queries on 2026-04-16, `src/postgres_ingest_binance.py`, `src/postgres_verify_data.py`]
3. **Wave 2: Build the cleaner/preparer.** Implement manifest parsing, per-symbol date/holdout selection, strict vs repair-capable cleaning, fixed-length window generation, sample-count reporting, and emitted bundle sidecars. This wave is the core of `MODEL-02`. [VERIFIED: `03-CONTEXT.md`, `src/train.py`, `src/postgres_materialize_dataset.py`]
4. **Wave 3: Wrap training and capture lineage.** Add a manual CLI that consumes a prepared bundle, records the explicit parent checkpoint and copied config, invokes the existing trainer, and writes a complete run bundle with checkpoint lineage and trainer outputs. [VERIFIED: `03-CONTEXT.md`, `src/main.py`, `src/train.py`]
5. **Wave 4: Add comparison/reporting and docs.** Link Phase 3 run bundles to Phase 2 backtest runs, produce repeatable comparison summaries, and update operator docs for the end-to-end manual retraining workflow. [VERIFIED: `03-CONTEXT.md`, `src/postgres_backtest.py`, `README.md`]

## Code Examples

Verified patterns from the current codebase:

### Current PostgreSQL Alignment Bridge
```python
# Source: src/postgres_materialize_dataset.py
pivot = frame.pivot(
    index="observation_time_utc",
    columns="series_label",
    values="close_price",
).sort_index()
pivot = pivot.dropna(axis=0, how="any")
return pivot.reset_index(drop=True)
```
[VERIFIED: `src/postgres_materialize_dataset.py`]

### Current Trainer Preprocessing Contract
```python
# Source: src/train.py
df = pd.read_csv(file_path, dtype='float64')
df = df.dropna(axis=1, how='any')
df = df.transpose()
df = df.sample(frac=1).reset_index(drop=True)
train_size = int(len(df) * train_ratio)
train_size -= train_size % batch_size
```
[VERIFIED: `src/train.py`]

### Current Backtest Comparison Link Surface
```python
# Source: src/postgres_backtest.py
stats_rows = postgres_backtest.query_backtest_step_stats(conn=conn, run_id=run_id)
```
[VERIFIED: `src/postgres_backtest.py`, `tests/test_postgres_backtest.py`]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TimesFM v1 / v2.0 JAX/PAX checkpoints loaded through the archived `v1` code path | Official upstream latest model is TimesFM `2.5`, with newer Torch/Flax examples and a LoRA fine-tuning example | Official repo updates on `2025-09-15` and `2026-04-09` | This repo is intentionally staying on the legacy v1 path, so Phase 3 should isolate a reliable v1 manual workflow instead of mixing in 2.5-era install or fine-tuning guidance. [CITED: https://github.com/google-research/timesfm/blob/master/README.md] |

**Deprecated/outdated:**
- Assuming "latest JAX" is safe for this repo is outdated; current PyPI `jax` latest requires Python `>=3.11`, while this project is intentionally pinned to Python `3.10` and TimesFM `1.3.0`. [VERIFIED: `.planning/PROJECT.md`, https://pypi.org/pypi/jax/json, https://pypi.org/pypi/timesfm/1.3.0/json]

## Assumptions Log

All material claims above were verified from the local repo, live local PostgreSQL state, or official upstream sources. No user-confirmation assumptions remain open in this research.

## Open Questions (RESOLVED)

1. **Parent checkpoint default**
   - Resolution: Phase 3 should not prefer any silent default. The manual wrapper must require an explicit operator-supplied parent checkpoint path or repo identity and record that choice in the run bundle.
   - Why this resolves the issue: `src/main.py` currently hides a Google base-checkpoint fallback, while the repo README presents a finance-tuned PFN checkpoint for operator-facing workflows. Requiring an explicit parent keeps lineage and later comparisons interpretable across both choices. [VERIFIED: `src/main.py`, `README.md`, https://huggingface.co/pfnet/timesfm-1.0-200m-fin, `.planning/phases/03-train-the-model-on-1-minute-crypto-candles/03-03-PLAN.md`]

2. **Known-good JAX/PAX/TensorFlow dependency set**
   - Resolution: Phase 3 should freeze the supported manual training environment in a checked-in `requirements.training.txt` generated by `03-03`, rooted in Python `3.10` and `timesfm[pax]==1.3.0`, and capture the actual resolved environment in each run bundle. Execution should not rely on unconstrained latest-package installs.
   - Why this resolves the issue: the repo lacks a lockfile today, but the planning decision is now explicit: environment composition is part of the deliverable, not an external assumption. That makes the training stack reproducible enough for a manual CLI phase without pretending the current host interpreter is already execution-ready. [VERIFIED: local tool probes on 2026-04-16, https://pypi.org/pypi/timesfm/1.3.0/json, `.planning/phases/03-train-the-model-on-1-minute-crypto-candles/03-03-PLAN.md`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Legacy training scripts and CLI tools | yes | `3.10.11` | - |
| Docker | PostgreSQL service and supported Windows-friendly runtime path | yes | `29.2.1` | WSL/Linux local runtime |
| Docker Compose | PostgreSQL service orchestration | yes | `v5.1.0` | `docker compose` only; no separate fallback needed |
| WSL | Supported Linux-like runtime on Windows host | yes | Default distro `Ubuntu`, WSL `2` | Docker |
| NVIDIA GPU | Practical acceleration path for `backend='gpu'` in `src/main.py` | yes | `RTX 4070 Laptop GPU`, driver `591.74` | CPU only after code/config change; current `src/main.py` hardcodes GPU |
| PostgreSQL service | Source candles and backtest metadata | yes | `postgres:18.3-bookworm` container, healthy on port `54329` | none for canonical flow |
| Local Python training deps (`timesfm`, `jax`, `paxml`, `praxis`, `tensorflow`, `pandas`) | Actual execution of Phase 3 scripts on the host Python | no | - | use a dedicated venv or WSL/Docker environment |
| Local Python test deps (`pytest`) | Automated verification on host Python | no | - | install `requirements.dev.txt` first |

**Missing dependencies with no fallback:**
- None for planning research itself, but actual host-side training execution is blocked until a full Python environment is installed. [VERIFIED: local `python -m pip show ...` probes on 2026-04-16]

**Missing dependencies with fallback:**
- Host Python lacks both runtime and test packages, but the machine has Docker, WSL2, and GPU support, so Phase 3 can still target a dedicated training environment rather than the bare host interpreter. [VERIFIED: local tool probes on 2026-04-16]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` `9.0.3` repo pin, with marker policy in `pytest.ini` |
| Config file | `pytest.ini` |
| Quick run command | `python -m pytest -q tests/test_training_preparer.py tests/test_training_workflow.py tests/test_training_lineage.py` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-01 | Manual training/evaluation workflow consumes PostgreSQL-selected bundles and records reproducible manifests instead of ad hoc file inputs | integration | `python -m pytest -q tests/test_training_workflow.py` | no - Wave 0 |
| MODEL-02 | Cleaner/preparer emits fixed-length model windows, explicit holdout metadata, and quality reports from PostgreSQL with consistent per-symbol selection rules | integration/contract | `python -m pytest -q tests/test_training_preparer.py tests/test_training_manifest.py` | no - Wave 0 |
| OPS-01 | Manual reruns preserve enough metadata to recreate the same dataset/training decision path after future data refreshes, without introducing scheduling yet | contract | `python -m pytest -q tests/test_training_lineage.py` | no - Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest -q tests/test_training_preparer.py tests/test_training_manifest.py`
- **Per wave merge:** `python -m pytest -q tests/test_training_preparer.py tests/test_training_manifest.py tests/test_training_workflow.py tests/test_training_lineage.py`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_training_preparer.py` - covers fixed-window emission, strict vs repair mode, per-symbol range handling, and quality report fields for `MODEL-02`
- [ ] `tests/test_training_manifest.py` - covers manifest schema validation, explicit holdout boundaries, and copied config/checkpoint metadata
- [ ] `tests/test_training_workflow.py` - covers wrapper invocation, parent checkpoint recording, and deterministic run-bundle layout for `MODEL-01`
- [ ] `tests/test_training_lineage.py` - covers backtest-run linkage and rerun reproducibility metadata for `OPS-01`
- [ ] Extend Docker-backed PostgreSQL fixtures if needed to seed BTC/ETH/SOL data with deliberate short gaps, long gaps, and missing-symbol cases
- [ ] Environment install for actual execution: `python -m pip install -r requirements.inference.txt -r requirements.dev.txt && python -m pip install "timesfm[pax]==1.3.0"`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | CLI-only local workflow; no auth surface added in this phase |
| V3 Session Management | no | No session layer in scope |
| V4 Access Control | no | No multi-user service or role model in scope |
| V5 Input Validation | yes | Validate manifest schema, symbol allowlist, ISO-UTC ranges, path targets, and use parameterized SQL through `psycopg` helpers. [VERIFIED: `src/postgres_dataset.py`, `src/postgres_discover_data.py`, `src/postgres_verify_data.py`] |
| V6 Cryptography | no | No custom cryptography should be introduced; rely on existing HTTPS downloads and recorded provenance instead. [VERIFIED: `src/postgres_ingest_binance.py`, `src/main.py`, https://huggingface.co/pfnet/timesfm-1.0-200m-fin] |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection through selector inputs | Tampering | Keep PostgreSQL reads parameterized, matching existing `psycopg` query style. [VERIFIED: `src/postgres_discover_data.py`, `src/postgres_verify_data.py`] |
| Holdout leakage through overlapping windows and random split | Tampering | Materialize explicit train and holdout bundles; do not trust the trainer's shuffled split. [VERIFIED: `src/train.py`, `03-CONTEXT.md`] |
| Unsafe artifact overwrites in `workdir` | Tampering | Use per-run directories and deterministic manifest filenames; do not reuse anonymous timestamp folders without copied metadata. [VERIFIED: `src/train.py`, `03-CONTEXT.md`] |
| Remote checkpoint/data provenance drift | Spoofing / Tampering | Record parent checkpoint ID, source coverage, ingestion ranges, and model-card/license references in the run bundle. [VERIFIED: `03-CONTEXT.md`, `src/main.py`, https://huggingface.co/pfnet/timesfm-1.0-200m-fin] |

## Sources

### Primary (HIGH confidence)

- Local repo evidence: `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/postgres_ingest_binance.py`, `src/postgres_verify_data.py`, `src/postgres_materialize_dataset.py`, `src/postgres_dataset.py`, `src/postgres_backtest.py`, `configs/fine_tuning.py`, `README.md`, `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `03-CONTEXT.md`
- Official TimesFM README: https://github.com/google-research/timesfm/blob/master/README.md
- Official TimesFM PyPI metadata: https://pypi.org/pypi/timesfm/1.3.0/json
- Official JAX PyPI metadata: https://pypi.org/pypi/jax/json
- Official PaxML PyPI metadata: https://pypi.org/pypi/paxml/json
- Official Psycopg PyPI metadata: https://pypi.org/pypi/psycopg/json
- Official PFN finance checkpoint model card: https://huggingface.co/pfnet/timesfm-1.0-200m-fin
- Live local PostgreSQL queries executed through `docker compose exec postgres psql` on 2026-04-16

### Secondary (MEDIUM confidence)

- None needed; the phase-critical claims were resolved from official sources and local evidence.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - official upstream sources verify the legacy TimesFM v1 path, but the repo still lacks a checked-in known-good full JAX/PAX lockfile for the training environment.
- Architecture: MEDIUM - the manifest-first bundle recommendation is strongly supported by repo constraints and code realities, but implementation details still depend on one explicit parent-checkpoint decision.
- Pitfalls: HIGH - the main risks are directly visible in current code (`src/train.py`, `src/postgres_materialize_dataset.py`) and in live PostgreSQL state.

**Research date:** 2026-04-16  
**Valid until:** 2026-05-16 or until the training runtime or PostgreSQL data contract changes materially
