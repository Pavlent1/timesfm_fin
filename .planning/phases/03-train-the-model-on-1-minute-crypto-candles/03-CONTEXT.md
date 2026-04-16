# Phase 3: Train the model on 1-minute crypto candles - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 expands the PostgreSQL crypto minute dataset and turns the existing TimesFM v1 fine-tuning path into a repeatable manual workflow for training on prepared 1-minute Binance crypto candles. The phase covers data expansion, dataset cleaning/preparation for model consumption, manual recurring fine-tune runs with custom date inputs, and snapshot/version tracking of resulting weights. Always-on scheduling, unattended retraining, and broader symbol expansion stay out of scope.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and product constraints
- `.planning/ROADMAP.md` - Phase 3 scope anchor and dependency on the PostgreSQL-backed backtest/data foundation from earlier phases.
- `.planning/PROJECT.md` - CLI-first product shape, TimesFM v1 compatibility target, Linux/WSL/Docker runtime constraint, and the repo-wide reproducibility priority.
- `.planning/REQUIREMENTS.md` - `MODEL-01`, `MODEL-02`, `OPS-01`, and the existing database/backtest requirements that shape how Phase 3 should build on PostgreSQL rather than bypass it.
- `.planning/STATE.md` - Current project state and the active sequencing around Phases 2 and 3.

### Prior phase decisions to inherit
- `.planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md` - Locks PostgreSQL as the dataset foundation and already states that later backtest/fine-tuning work should consume PostgreSQL-backed minute data.
- `.planning/phases/02-create-backtest-architecture-qualification-rules-and-statist/02-CONTEXT.md` - Locks PostgreSQL as the canonical store for backtests and explains why training holdouts and later comparisons should stay reproducible against that shared data foundation.

### Existing data pipeline and preparation baseline
- `README.md` - Current Phase 1 and Phase 2 user-facing workflows, including PostgreSQL ingestion/materialization and the existing fine-tuning entrypoint.
- `src/postgres_ingest_binance.py` - Existing Binance-to-PostgreSQL ingestion path that Phase 3 must extend from one symbol/window to the larger multi-symbol coverage target.
- `src/postgres_verify_data.py` - Existing integrity verification baseline that should inform the new cleaner/preparer quality reporting path.
- `src/postgres_discover_data.py` - Existing visibility into dataset coverage that will help validate training and holdout ranges.
- `src/postgres_materialize_dataset.py` - Current bridge from PostgreSQL observations into model-facing CSV shapes, including the existing `training_matrix` export.
- `src/postgres_dataset.py` - Shared PostgreSQL connection, schema bootstrap, series registration, provenance, and observation upsert helpers.

### Existing training and evaluation path
- `src/main.py` - Current fine-tuning CLI entrypoint and checkpoint-loading contract.
- `src/train.py` - Current training preprocessing assumptions, batch construction, and checkpoint-writing behavior.
- `src/evaluation.py` - Current checkpoint evaluation flow that Phase 3 may reuse for snapshot comparison.
- `configs/fine_tuning.py` - Current fine-tuning hyperparameter source that snapshot metadata must capture.
- `.planning/codebase/ARCHITECTURE.md` - Current flat CLI architecture and the split between PostgreSQL-backed data workflows and legacy training.
- `.planning/codebase/STACK.md` - Runtime and dependency constraints for the TimesFM v1 / JAX / PaxML stack.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/postgres_ingest_binance.py`: already supports Binance spot candle ingestion into PostgreSQL and can be extended to cover the larger BTC/ETH/SOL history windows.
- `src/postgres_verify_data.py`: already computes integrity-oriented dataset checks and should inform the Phase 3 quality-report layer.
- `src/postgres_materialize_dataset.py`: already exports aligned numeric training matrices from PostgreSQL and is the clearest current bridge into the legacy trainer.
- `src/main.py`: already defines the existing fine-tune/eval CLI and the checkpoint parent selection path.
- `src/train.py`: already contains the model-facing preprocessing and checkpoint save behavior that Phase 3 must feed rather than replace blindly.
- `src/evaluation.py`: already provides a checkpoint evaluation path that can support snapshot comparison workflows.

### Established Patterns
- The repo is still CLI-first, so recurring training should be expressed as manual Python/PowerShell/Docker commands rather than a background service.
- PostgreSQL is the canonical source of crypto minute data and backtest facts; Phase 3 should build on that shared store rather than introduce a second training-only source of truth.
- The current trainer consumes prepared CSV-like input rather than raw candles or direct SQL query streams, so a preparation/materialization boundary is part of the existing architecture.
- Checkpoints already live under a user-provided work directory, but there is no first-class lineage or experiment manifest yet.

### Integration Points
- Extend the PostgreSQL ingestion/discovery workflow to guarantee the required BTC/ETH/SOL coverage windows.
- Insert a new cleaner/preparer stage between PostgreSQL dataset selection and the existing fine-tuning entrypoint.
- Add a manual recurring-training CLI that accepts explicit per-symbol date and holdout inputs, then feeds the prepared dataset into `src/main.py`.
- Attach snapshot metadata and comparison outputs to the resulting checkpoint artifacts so later backtests and evaluations can be tied back to the exact training slice used.

</code_context>

<specifics>
## Specific Ideas

- The user wants the first fine-tune experiment to use one month of data from each of `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`.
- Bitcoin keeps more source history than the other pairs because the latest four months are intentionally preserved for backtests.
- The user explicitly wants to compare how later added training data changes results over time, so run lineage and snapshot comparisons matter as much as raw checkpoint saving.
- The user explicitly expects research to determine how raw minute candles must be cleaned and transformed before the current TimesFM training stack can consume them safely.

</specifics>

<deferred>
## Deferred Ideas

- Automatic or scheduled retraining is deferred to a later phase.
- Expanding beyond `BTCUSDT`, `ETHUSDT`, and `SOLUSDT` is deferred until this repeatable three-pair workflow is proven.
- Broader model-serving or hosted orchestration remains out of scope; Phase 3 stays a local manual workflow.

</deferred>

---

*Phase: 03-train-the-model-on-1-minute-crypto-candles*
*Context gathered: 2026-04-16*
