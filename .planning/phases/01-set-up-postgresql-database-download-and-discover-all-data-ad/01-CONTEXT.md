# Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes a Docker-managed PostgreSQL data foundation for the repository so project workflows can ingest, store, inspect, sort, organize, and validate historical market data in a repeatable way. This phase must do more than stand up the database: it must produce a practical path for later backtest and fine-tuning work to consume PostgreSQL-backed data, while staying focused on batch/CLI workflows rather than dashboards, services, or live streaming infrastructure.

</domain>

<decisions>
## Implementation Decisions

### PostgreSQL setup
- **D-01:** Standardize on a local Docker-based PostgreSQL setup owned by the repository, with a YAML-based container definition rather than ad hoc manual setup.
- **D-02:** Phase 1 should provide one documented, repo-native setup path that project scripts can rely on from the supported local runtime story.

### Data model and ingestion scope
- **D-03:** Design the schema for multiple assets/symbols from the start rather than hard-coding a BTC-only structure.
- **D-04:** The initial stored data type is intentionally narrow: 1-minute candle close-price time-series data is enough for Phase 1.
- **D-05:** The first concrete ingestion workflow is a one-time script that downloads and stores about the past 1 year of Binance `BTCUSDT` 1-minute close-price data.
- **D-06:** The data layer must support storing different datasets such as multi-year BTC and SOL minute histories in the same system later, even though the first loader targets only Bitcoin.
- **D-07:** Ingestion must be rerunnable without creating duplicate observations or silently corrupting existing data, and it must preserve dataset provenance and coverage metadata.

### Discovery and integrity
- **D-08:** Dataset discovery in Phase 1 should be script-driven, not SQL-docs-only. Users should be able to inspect what data exists through project commands or scripts.
- **D-09:** Phase 1 must include scripts for data integrity verification because cleaner data is treated as directly important for better model and backtest results.
- **D-10:** Integrity verification must check at least duplicate timestamps, missing minute gaps, ordering problems, null values, out-of-range timestamps, and coverage summaries.
- **D-11:** Discovery/reporting should support filtering and sorting stored data by source, symbol, timeframe, and date range.

### Training and backtest path
- **D-12:** Phase 1 must include a working path from PostgreSQL-backed data into later backtest and fine-tuning workflows; this should not stop at raw storage only.

### the agent's Discretion
- The exact first bridge from PostgreSQL into existing CSV-driven training/backtest code is left to the agent's discretion during planning.
- Favor the simplest reliable path that works in this codebase, whether that is a PostgreSQL-to-CSV/materialized dataset step, a reusable database extraction layer, or a direct PostgreSQL reader for one workflow.
- The initial implementation does not need to generalize beyond 1-minute close-price datasets as long as the schema is not painted into a corner for additional symbols later.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` - Phase 1 goal, success criteria, and scope anchor for the PostgreSQL data foundation.
- `.planning/REQUIREMENTS.md` - `DB-01` through `DISC-03` define the required setup, ingestion, provenance, discovery, and documentation outcomes; `MODEL-01` and `MODEL-02` explain the later PostgreSQL-backed modeling direction this phase must not block.
- `.planning/PROJECT.md` - Project constraints, CLI-first product shape, Docker/Linux runtime expectation, and the decision to start with a PostgreSQL-backed data foundation.
- `.planning/STATE.md` - Current project status and the note that later phases depend on clarifying this data-foundation direction.

### Existing runtime baseline
- `README.md` - Current user-facing workflow, especially the Binance + SQLite backtest path and the repo's Docker/WSL runtime posture.
- `.planning/codebase/ARCHITECTURE.md` - Current script-oriented architecture, including the inference/backtest path and where a new data layer must connect.
- `.planning/codebase/STRUCTURE.md` - Where new CLI modules, scripts, and config should live in the current flat repository layout.
- `.planning/codebase/STACK.md` - Current runtime and dependency constraints, including Docker, Python 3.10, and the lack of an existing PostgreSQL stack.
- `.planning/codebase/CONCERNS.md` - Existing fragility in `src/crypto_minute_backtest.py`, missing tests, and reproducibility risks that should shape the Phase 1 design.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crypto_minute_backtest.py`: Already contains Binance pagination, UTC timestamp handling, CLI argument patterns, and a persistence boundary that can be refactored from SQLite toward PostgreSQL-backed ingestion and reporting.
- `scripts/run_crypto_backtest.ps1`: Provides an existing Docker-oriented Windows wrapper pattern that can inform PostgreSQL helper scripts and container orchestration expectations.
- `src/main.py` and `src/train.py`: Show the current CSV-oriented fine-tuning entrypoints that the PostgreSQL data layer must eventually feed or bridge into.
- `src/run_forecast.py` and `src/evaluate_forecast.py`: Provide the existing CLI style and validation conventions to match for new PostgreSQL discovery/materialization tools.

### Established Patterns
- The repo is CLI-first and script-oriented; new user workflows should be exposed through Python entrypoints under `src/` and helper scripts under `scripts/`.
- Docker is already the practical Windows-friendly runtime pattern for heavyweight workflows in this repository.
- Storage logic currently lives inside runtime scripts instead of a shared data-access layer, so planning should expect some extraction/refactoring work rather than only additive code.
- The codebase uses a flat `src/` namespace with direct module imports, not a packaged application layout.

### Integration Points
- Replace or extract the SQLite-specific storage functions in `src/crypto_minute_backtest.py` into a reusable PostgreSQL-oriented ingestion/storage path.
- Add PostgreSQL setup/orchestration artifacts alongside the existing Docker and PowerShell workflow.
- Add a discovery/reporting path that can inspect available datasets and integrity status without requiring manual SQL.
- Provide a reliable bridge from PostgreSQL-stored time-series data into the current training/backtest workflow shape used by `src/main.py`, `src/train.py`, and related CLI tools.

</code_context>

<specifics>
## Specific Ideas

- The system should support storing multiple assets in the same database, for example several years of BTC and SOL 1-minute close-price data.
- The first ingestion workflow should be a one-time run script focused on downloading Binance Bitcoin data for roughly the past year.
- The user explicitly prioritizes data cleanliness and wants strong integrity verification because cleaner data is expected to improve downstream results.
- The user is open to the agent choosing the best integration shape for the first PostgreSQL-to-model bridge as long as it works reliably.

</specifics>

<deferred>
## Deferred Ideas

- Recurring scheduled refreshes into PostgreSQL are not the immediate target for this first one-time ingestion workflow.
- Real-time or streaming ingestion remains out of scope for v1.
- Broader candle fields or additional market-data shapes beyond 1-minute close-price series can come after the initial schema foundation is proven.
- Full first-class PostgreSQL-native forecasting/training execution across all existing workflows may extend beyond Phase 1, as long as this phase delivers a working bridge and does not block that path.

</deferred>

---

*Phase: 01-set-up-postgresql-database-download-and-discover-all-data-ad*
*Context gathered: 2026-04-13*
