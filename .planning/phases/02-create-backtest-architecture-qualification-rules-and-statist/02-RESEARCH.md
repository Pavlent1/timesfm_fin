# Phase 2: Create backtest architecture, qualification rules, and statistics collection - Research

**Researched:** 2026-04-14  
**Domain:** PostgreSQL-backed backtest persistence, per-step forecast analytics, and CLI/runtime migration for the crypto minute backtest  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** PostgreSQL is the single canonical database for everything in this repository, including source candles, backtest runs, and backtest statistics. Phase 2 should not preserve SQLite as the primary backtest store.
- **D-02:** The backtest data model should be optimized for querying from the database later, not just for one script run. The storage grain must support efficient retrieval of run-level, window-level, and per-output-candle statistics.
- **D-03:** Persist one database row for every predicted output candle step of every evaluated window. This is the required base fact model for later optimized analysis.
- **D-04:** Step-level storage should capture enough raw facts to recompute or extend metrics later, including at minimum run identity, window identity, horizon step index, timestamps, last input candle close, predicted close, and actual close.
- **D-05:** Per-step aggregate statistics should be queryable directly from PostgreSQL so the user can inspect how performance changes as the prediction horizon gets farther from the context window.
- **D-06:** Statistics must be gathered individually for each predicted output candle position in the horizon rather than only as one run-level summary.
- **D-07:** The primary "accuracy" metric for this phase is the normalized deviation from a perfect prediction, computed from the price ratio against the actual candle: `abs((predicted_close / actual_close) - 1.0) * 100`.
- **D-08:** The standard deviation of accuracy must use that same normalized accuracy metric from `D-07`, grouped per predicted output candle position across the run.
- **D-09:** Overshoot and undershoot must be stored both as a classification label and as a signed deviation value so later queries can use either form.
- **D-10:** Overshoot and undershoot are judged relative to the last correct input candle close, meaning the closing price of the final candle in the input context window.
- **D-11:** The rule compares the predicted candle and the actual candle against that last input close. If the actual candle closes above the last input close, a prediction above the actual close is an overshoot and a prediction below the actual close is an undershoot. If the actual candle closes below the last input close, a prediction below the actual close is an overshoot and a prediction above the actual close is an undershoot.
- **D-12:** Overshoot and undershoot magnitudes must also be stored as percentages relative to the actual price.
- **D-13:** Because signed storage is required, the database design should support a signed percent deviation where overshoot is positive and undershoot is negative, while also preserving an explicit categorical label.
- **D-14:** The "qualification rules" wording in the roadmap is not a separate user requirement for a distinct rule engine in this phase. The intended work is the backtest data structure plus the statistics and metric collection pipeline.

### the agent's Discretion
- Keep the exact table and view names implementation-owned as long as run, window, and step queries stay straightforward.
- Decide whether per-step aggregates are plain SQL views or materialized views.
- Choose whether the runtime reads source candles only from PostgreSQL or fetches live data and persists it into PostgreSQL first, provided SQLite stops being canonical.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BT-01 | User can run the crypto minute backtest with PostgreSQL as the canonical store for backtest runs, windows, and per-step prediction facts. | The repo already has shared PostgreSQL settings/bootstrap helpers in `src/postgres_dataset.py`, so the backtest runtime should reuse that path instead of carrying a second `sqlite3` persistence layer. [VERIFIED: `src/postgres_dataset.py`, `src/crypto_minute_backtest.py`] |
| BT-02 | User can query per-output-candle backtest statistics directly from PostgreSQL so horizon-distance behavior is inspectable without manual recomputation. | PostgreSQL views execute the stored query at read time, which fits low-latency aggregate inspection on top of raw step facts without adding refresh choreography yet. [CITED: https://www.postgresql.org/docs/current/sql-createview.html] |
| BT-03 | User can inspect overshoot and undershoot outcomes using the locked context-relative classification and signed percent deviation rules. | The current code stores only per-window JSON payloads and run-level summaries, so Phase 2 needs a reusable metric layer plus step-grain columns that lock the new semantics into storage. [VERIFIED: `src/crypto_minute_backtest.py`, `tests/test_crypto_minute_backtest.py`] |
| BT-04 | User can reproduce a stored backtest result from recorded run metadata, model settings, and source data coverage. | PostgreSQL `INSERT ... ON CONFLICT` plus `RETURNING` support a deterministic helper layer for run/window/step records and provenance-oriented metadata capture. [CITED: https://www.postgresql.org/docs/current/sql-insert.html] [VERIFIED: `src/postgres_dataset.py`] |
| BT-05 | User can rely on automated tests to catch regressions in backtest metric semantics and PostgreSQL persistence. | The repo already uses `pytest` for the current backtest script and PowerShell wrapper tests, so the safest Phase 2 path is to extend that suite with metric-contract and PostgreSQL integration coverage. [VERIFIED: `tests/test_crypto_minute_backtest.py`, `tests/test_script_wrappers.py`] |
</phase_requirements>

## Summary

Phase 2 should not be planned as a direct "swap `sqlite3` for `psycopg`" inside `src/crypto_minute_backtest.py`. The current script mixes CLI parsing, Binance fetches, persistence, metrics, and reporting in one file, and its stored data shape is one row per forecast window plus a run summary. That shape cannot satisfy the locked requirement to analyze every horizon step directly from PostgreSQL. [VERIFIED: `src/crypto_minute_backtest.py`]

The lowest-risk architecture is:

1. Keep PostgreSQL as the only durable store and extend the existing Phase 1 bootstrap path with backtest-specific tables.
2. Introduce a reusable metric module that computes normalized deviation, overshoot/undershoot classification, signed percent deviation, and per-step aggregates from raw step facts.
3. Persist three layers of backtest data: run metadata, window metadata, and one step-fact row per predicted candle.
4. Expose a plain SQL view for per-step aggregate stats first, because PostgreSQL views re-run the underlying query on access while materialized views require refresh management yet. Given the current default scale, query-time aggregation is the better default. [CITED: https://www.postgresql.org/docs/current/sql-createview.html] [CITED: https://www.postgresql.org/docs/current/sql-creatematerializedview.html]
5. Migrate the runtime and wrapper so PostgreSQL-backed source data and backtest artifacts share the same connection path, and stop presenting SQLite as canonical in docs or CLI help.

## Current Code Reality

### What exists now

- `src/crypto_minute_backtest.py` owns SQLite schema creation, candle persistence, metrics, backtest execution, and CLI/reporting.
- `tests/test_crypto_minute_backtest.py` currently validates the SQLite-centric behavior with in-memory databases.
- `scripts/run_crypto_backtest.ps1` passes `--db-path` into the Dockerized runtime and assumes the backtest store is a local SQLite file.
- `src/postgres_dataset.py` already centralizes PostgreSQL settings, connection, bootstrap, and ingestion helpers from Phase 1.

### Why the current shape is insufficient

- `backtest_predictions` stores one row per window, not per horizon step.
- Overshoot and undershoot are not modeled at all.
- The accuracy metric is still expressed through MAE/RMSE/MAPE/SMAPE and directional accuracy, not the locked normalized-deviation metric.
- The wrapper and README still tell the user to treat `outputs/crypto_backtest.sqlite` as the experiment record of truth.

## Recommended Architecture

### PostgreSQL objects

Use checked-in schema SQL under `db/init/002_phase2_backtest_schema.sql` and keep the tables in the existing PostgreSQL namespace rather than creating another storage technology.

Recommended object set:

- `market_data.backtest_runs`
  - One row per completed or in-progress backtest run.
  - Stores model repo, backend, freq bucket, context/horizon/stride, source symbol/timeframe, time range, and created/completed timestamps.
- `market_data.backtest_windows`
  - One row per forecast origin.
  - Stores run identity, window index, target start, context end, and last input close.
- `market_data.backtest_prediction_steps`
  - One row per predicted horizon step for each window.
  - Stores `step_index`, target timestamp, predicted close, actual close, normalized deviation percent, signed deviation percent, and overshoot/undershoot label.
- `market_data.backtest_step_stats_vw`
  - Plain SQL view grouped by run and `step_index`.
  - Computes `avg_normalized_deviation_pct`, `stddev_normalized_deviation_pct`, overshoot/undershoot counts, and average signed deviation percent.

### Metric module

Create a new `src/backtest_metrics.py` module and move formula decisions there so both the runtime and storage helpers use the same definitions. That module should own:

- normalized deviation percent
- context-relative overshoot/undershoot classification
- signed percent deviation
- per-step aggregation inputs used by SQL contract tests and runtime assertions

### Runtime migration

The runtime should stop treating SQLite as a special data silo:

- Backtest mode should load source candles from PostgreSQL's Phase 1 dataset tables for the requested symbol/day/timeframe.
- Live mode may still fetch from Binance, but any fetched candles should be persisted into PostgreSQL through the existing ingestion helpers before forecasting or reporting.
- The script should call dedicated PostgreSQL storage helpers instead of embedding SQL DDL/DML inline.

## Views vs Materialized Views

Use a normal SQL view first.

Reasoning:

- PostgreSQL documents that normal views are not physically materialized and instead run the underlying query when referenced. [CITED: https://www.postgresql.org/docs/current/sql-createview.html]
- PostgreSQL documents that materialized views must be populated and later refreshed explicitly. [CITED: https://www.postgresql.org/docs/current/sql-creatematerializedview.html]
- The current default backtest scale is modest: with one UTC day of 1-minute candles, `context_len=512`, `horizon_len=16`, and `stride=1`, the current implementation produces 913 forecast windows. Under the locked Phase 2 storage grain, that becomes about 14,608 step rows per run, which does not justify refresh management yet. [INFERRED from `src/crypto_minute_backtest.py` defaults and window math]

Recommendation:

- Start with `market_data.backtest_step_stats_vw`.
- Revisit a materialized view only if multi-symbol or multi-day studies make query latency measurable.

## Runtime/Wrapper Integration Risk

The Docker wrapper currently runs the Python CLI in a standalone container. Once the runtime depends on PostgreSQL, the container must be able to reach the host or compose-managed database.

Recommended Phase 2 handling:

- Keep the PowerShell wrapper, but inject PostgreSQL env vars into `docker run`.
- Use `POSTGRES_HOST=host.docker.internal` in the container path and add `--add-host=host.docker.internal:host-gateway` for Linux-compatible Docker setups.
- Keep the default local Python/WSL path aligned with the existing `src/postgres_dataset.py` defaults.

This avoids inventing a second wrapper just for PostgreSQL and keeps the user-facing command surface small.

## Pitfalls To Avoid

### Pitfall 1: Store only derived stats and drop raw step facts

That would violate `D-03` and make later metric changes impossible without rerunning the model. Raw step facts must remain the source of truth.

### Pitfall 2: Keep formulas duplicated between Python and SQL

If Python computes one overshoot rule and the SQL view aggregates another interpretation, the phase will look correct in unit tests but produce inconsistent analytics. Put formulas in a reusable Python module and mirror them explicitly in schema/view tests.

### Pitfall 3: Keep `--db-path` as a "temporary" escape hatch

The phase goal is one canonical database. Leaving a first-class SQLite flag in the main backtest path preserves the split-brain storage model the user rejected.

### Pitfall 4: Use materialized views before there is a measured query problem

Materialized views add refresh semantics and stale-data failure modes. For this phase the requirement is queryability, not precomputed warehouse behavior.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` |
| Config file | none detected |
| Quick run command | `python -m pytest -q tests/test_backtest_metrics.py tests/test_postgres_backtest.py tests/test_crypto_minute_backtest.py tests/test_script_wrappers.py tests/test_docs_contract.py` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BT-01 | PostgreSQL stores run/window/step facts for a backtest run | integration | `python -m pytest -q tests/test_postgres_backtest.py::test_save_backtest_writes_run_window_and_step_rows` | ❌ Wave 0 for Phase 2 |
| BT-02 | Per-step stats view exposes aggregate metrics by horizon step | integration | `python -m pytest -q tests/test_postgres_backtest.py::test_step_stats_view_aggregates_by_run_and_step` | ❌ Wave 0 for Phase 2 |
| BT-03 | Overshoot/undershoot and normalized deviation formulas match locked rules | unit | `python -m pytest -q tests/test_backtest_metrics.py` | ❌ Wave 0 for Phase 2 |
| BT-04 | Runtime stores reproducible run metadata and source coverage | integration | `python -m pytest -q tests/test_crypto_minute_backtest.py::test_backtest_uses_postgres_run_metadata` | ❌ Wave 0 for Phase 2 |
| BT-05 | Wrapper/docs/runtime contracts no longer advertise SQLite as canonical | contract | `python -m pytest -q tests/test_script_wrappers.py tests/test_docs_contract.py` | ⭕ existing files need extension |

## Sources

### Primary

- PostgreSQL `CREATE VIEW` docs: https://www.postgresql.org/docs/current/sql-createview.html
- PostgreSQL `CREATE MATERIALIZED VIEW` docs: https://www.postgresql.org/docs/current/sql-creatematerializedview.html
- PostgreSQL `INSERT` docs: https://www.postgresql.org/docs/current/sql-insert.html
- Psycopg basic usage docs: https://www.psycopg.org/psycopg3/docs/basic/usage.html
- Local repo evidence from `src/crypto_minute_backtest.py`, `src/postgres_dataset.py`, `tests/test_crypto_minute_backtest.py`, `tests/test_script_wrappers.py`, and `README.md`

### Inferences

- Query-time SQL views are the right default for Phase 2 because the current run scale is small enough that refresh management would be unnecessary operational overhead.
- The safest refactor boundary is a dedicated metric module plus PostgreSQL storage helper module, not another round of inline SQL inside the monolithic runtime script.

---
*Research date: 2026-04-14*
*Valid until re-planning or a material runtime/storage change*
