# Phase 2: create-backtest-architecture-qualification-rules-and-statist - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 establishes the PostgreSQL-backed backtest information structure for the repository and defines the statistics pipeline used to evaluate forecast quality. The phase must replace the current split persistence story with one canonical database for both collected market data and backtest artifacts, and it must make per-horizon analysis practical by storing and aggregating metrics for each predicted output candle position.

</domain>

<decisions>
## Implementation Decisions

### Canonical backtest storage
- **D-01:** PostgreSQL is the single canonical database for everything in this repository, including source candles, backtest runs, and backtest statistics. Phase 2 should not preserve SQLite as the primary backtest store.
- **D-02:** The backtest data model should be optimized for querying from the database later, not just for one script run. The storage grain must support efficient retrieval of run-level, window-level, and per-output-candle statistics.

### Persistence grain
- **D-03:** Persist one database row for every predicted output candle step of every evaluated window. This is the required base fact model for later optimized analysis.
- **D-04:** Step-level storage should capture enough raw facts to recompute or extend metrics later, including at minimum run identity, window identity, horizon step index, timestamps, last input candle close, predicted close, and actual close.
- **D-05:** Per-step aggregate statistics should be queryable directly from PostgreSQL so the user can inspect how performance changes as the prediction horizon gets farther from the context window.

### Metric semantics
- **D-06:** Statistics must be gathered individually for each predicted output candle position in the horizon rather than only as one run-level summary.
- **D-07:** The primary "accuracy" metric for this phase is the normalized deviation from a perfect prediction, computed from the price ratio against the actual candle: `abs((predicted_close / actual_close) - 1.0) * 100`.
- **D-08:** The standard deviation of accuracy must use that same normalized accuracy metric from `D-07`, grouped per predicted output candle position across the run.
- **D-09:** Overshoot and undershoot must be stored both as a classification label and as a signed deviation value so later queries can use either form.

### Overshoot and undershoot rules
- **D-10:** Overshoot and undershoot are judged relative to the last correct input candle close, meaning the closing price of the final candle in the input context window.
- **D-11:** The rule compares the predicted candle and the actual candle against that last input close. If the actual candle closes above the last input close, a prediction above the actual close is an overshoot and a prediction below the actual close is an undershoot. If the actual candle closes below the last input close, a prediction below the actual close is an overshoot and a prediction above the actual close is an undershoot.
- **D-12:** Overshoot and undershoot magnitudes must also be stored as percentages relative to the actual price.
- **D-13:** Because signed storage is required, the database design should support a signed percent deviation where overshoot is positive and undershoot is negative, while also preserving an explicit categorical label.

### Phase naming clarification
- **D-14:** The "qualification rules" wording in the roadmap is not a separate user requirement for a distinct rule engine in this phase. The intended work is the backtest data structure plus the statistics and metric collection pipeline.

### the agent's Discretion
- The exact PostgreSQL table names, view names, and index strategy are left to the agent as long as the resulting structure clearly supports efficient run, window, and step queries.
- Exact handling for perfect predictions and neutral/no-move candles can be formalized during planning, but exact matches should naturally produce zero normalized deviation.
- The planner can choose whether per-step aggregates are materialized tables, SQL views, or query-time rollups, as long as the raw step facts remain available.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and prior decisions
- `.planning/ROADMAP.md` - Phase 2 scope anchor and the roadmap wording for backtest architecture and statistics collection.
- `.planning/PROJECT.md` - Core product constraints: CLI-first workflows, trust/reproducibility priority, and the existing TimesFM v1 runtime boundary.
- `.planning/REQUIREMENTS.md` - Current validated database requirements and the `MODEL-01` / `MODEL-02` direction for running modeling workflows on top of PostgreSQL-backed datasets.
- `.planning/STATE.md` - Current project status showing Phase 2 as the active planning target.
- `.planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md` - Locked Phase 1 decisions that PostgreSQL is the project data foundation and later backtest work should build on it instead of introducing a separate long-term store.

### Existing runtime and code constraints
- `README.md` - Current user-facing backtest and forecast workflow expectations.
- `.planning/codebase/ARCHITECTURE.md` - Current flat CLI architecture and the existing crypto backtest path.
- `.planning/codebase/CONCERNS.md` - Known fragility of `src/crypto_minute_backtest.py`, current metric risks, and missing automated test coverage.
- `.planning/codebase/INTEGRATIONS.md` - Current external dependencies and the existing SQLite persistence boundary in the backtest flow.
- `src/crypto_minute_backtest.py` - Current backtest runtime, SQLite schema, per-window persistence approach, and existing summary metrics.
- `src/evaluate_forecast.py` - Existing reusable metric helpers and rolling-evaluation metric style.

### PostgreSQL foundation to build on
- `src/postgres_dataset.py` - Shared PostgreSQL connection, schema bootstrap, and ingestion-run helpers added in Phase 1.
- `src/postgres_materialize_dataset.py` - Current PostgreSQL-to-CSV bridge that shows how Phase 1 data already feeds modeling workflows.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/postgres_dataset.py`: already provides the shared PostgreSQL connection path and schema bootstrap conventions that Phase 2 should extend instead of creating a parallel database layer.
- `src/postgres_materialize_dataset.py`: shows the current bridge from PostgreSQL data into model-facing workflows and reinforces the direction that backtest infrastructure should stay aligned with PostgreSQL.
- `src/crypto_minute_backtest.py`: already contains the runtime batching logic, window indexing, forecast generation, and persistence boundary that can be refactored from SQLite into PostgreSQL-backed storage.
- `src/evaluate_forecast.py`: already defines simple metric helpers and the repo's current evaluation terminology.

### Established Patterns
- The repository remains CLI-first and script-oriented, so Phase 2 should expose backtest/statistics behavior through Python entrypoints rather than a service or dashboard.
- PostgreSQL is already the chosen durable data store for project datasets after Phase 1; new backtest persistence should extend that decision instead of reintroducing a second canonical database.
- The current backtest script is monolithic, so planning should expect both schema work and code extraction/refactoring work rather than only additive SQL.

### Integration Points
- Replace the SQLite-only persistence path in `src/crypto_minute_backtest.py` with PostgreSQL-backed run, window, and step storage.
- Keep the forecasting engine reusable while moving persistence and statistics concerns behind clearer module boundaries.
- Add queryable per-step statistics that make horizon-distance analysis straightforward from PostgreSQL.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly wants one database for everything rather than a split PostgreSQL-plus-SQLite model.
- The user wants the raw persistence grain to be one stored row per predicted output candle step for every evaluated window.
- The main analytic goal is to see how prediction quality changes depending on how far the forecast is from the input context window.
- The user-defined normalized accuracy metric is not the raw `predicted / actual` ratio; it is the percent deviation from perfect prediction based on that ratio.
- Overshoot and undershoot must be measurable both categorically and numerically, with percentages relative to the actual price and logic anchored to the last input candle close.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 02-create-backtest-architecture-qualification-rules-and-statist*
*Context gathered: 2026-04-14*
