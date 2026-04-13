# Architecture Research

**Domain:** Financial time-series forecasting and backtesting toolkit
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
+-----------------------------------------------------------+
| CLI and Script Entry Points                               |
| run_forecast | evaluate_forecast | crypto_backtest | main |
+--------------------------+--------------------------------+
                           |
                           v
+-----------------------------------------------------------+
| Shared Runtime Services                                   |
| argument validation | data loading | model adapter        |
| metric helpers | output formatting | persistence helpers  |
+--------------------------+--------------------------------+
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
+---------------------------+   +----------------------------+
| TimesFM Model Runtime     |   | Persistence and Artifacts  |
| forecast / train / eval   |   | CSV outputs | SQLite | logs|
+---------------------------+   +----------------------------+
          |
          v
+-----------------------------------------------------------+
| External Inputs                                            |
| CSV files | Yahoo Finance | Binance | Hugging Face model   |
+-----------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI entrypoints | Parse flags, validate mode-specific arguments, and hand work to shared helpers | Thin `argparse` or `absl.flags` modules |
| Dataset loaders | Normalize CSV and remote market data into one series contract | Shared loader module with explicit schema and validation |
| Model adapter | Hide TimesFM checkpoint construction and backend selection details | One small adapter boundary wrapping TimesFM-specific objects |
| Metric layer | Compute forecast metrics once, consistently, and under test | Shared pure functions with fixture-based tests |
| Persistence layer | Write forecast outputs, run metadata, and backtest history | CSV writers for simple runs, SQLite for experiment history |

## Recommended Project Structure

```text
src/
|-- cli/                  # Optional future home for thin entrypoint wrappers
|-- data/                 # Shared CSV and market-data loaders plus validation
|-- model/                # TimesFM adapter and runtime selection
|-- metrics/              # Shared metric math under test
|-- persistence/          # CSV and SQLite output helpers
|-- training/             # Fine-tuning specific orchestration
`-- legacy/               # Deprecated or experimental workflows kept isolated
```

### Structure Rationale

- **Shared service modules first:** the repo currently repeats validation and metric logic across files; centralizing the reusable pieces reduces drift.
- **Thin CLIs:** entrypoints should stay focused on argument handling and user messaging, not business logic.
- **Legacy isolation:** experimental and deprecated paths should not shape the main runtime contract.

## Architectural Patterns

### Pattern 1: Thin CLI + Shared Service Layer

**What:** Keep each user-facing command small and move reusable behavior into importable helpers.
**When to use:** For forecast, evaluation, and backtest entrypoints that share loaders and model setup.
**Trade-offs:** Slightly more file structure, but much lower duplication and easier tests.

### Pattern 2: Adapter Boundary Around TimesFM

**What:** Concentrate checkpoint construction, backend selection, and model invocation behind one adapter.
**When to use:** Any time the code touches TimesFM runtime details.
**Trade-offs:** Adds an abstraction layer, but makes later migration or fallback work far safer.

### Pattern 3: Explicit Data Contract at the Boundary

**What:** Validate date column, target column, ordering, minimum history, and positivity assumptions before the model path starts.
**When to use:** For every CSV or remote-series ingest path.
**Trade-offs:** More up-front validation code, but clearer failures and safer metrics.

## Data Flow

### Request Flow

```text
User command
    ->
CLI parser
    ->
input validation and loader
    ->
model adapter
    ->
forecast / evaluation / backtest loop
    ->
metrics and persistence
    ->
console summary + artifacts
```

### Key Data Flows

1. **Single forecast:** One normalized series enters the model adapter and exits as a prediction table plus optional CSV artifact.
2. **Rolling evaluation:** Many contexts are derived from one normalized series, forecasted, then aggregated into benchmark metrics.
3. **Crypto backtest:** Remote candles are fetched or loaded, persisted, batch-forecasted, summarized, and recorded as run history.
4. **Fine-tuning:** Dataset preprocessing feeds the legacy JAX/PAX learner, which writes logs and checkpoints under a user-supplied work directory.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single-user local experiments | Monolithic CLI scripts are acceptable if validation and metrics are shared |
| Frequent repeated backtests | Batch forecast windows, isolate persistence, and track provenance for run comparison |
| Multi-symbol / longer-horizon studies | Separate orchestration from storage and avoid one-model-call-per-window loops |

### Scaling Priorities

1. **First bottleneck:** rolling evaluation throughput - batch contexts before looking for deeper optimization.
2. **Second bottleneck:** crypto backtest maintainability - separate ingestion, persistence, and model code before adding more modes.

## Anti-Patterns

### Anti-Pattern 1: Monolithic Runtime Files

**What people do:** Put CLI parsing, network access, metrics, persistence, and model calls in one script.
**Why it's wrong:** Small changes become high-risk and hard to test.
**Do this instead:** Pull reusable logic into data, model, metrics, and persistence modules.

### Anti-Pattern 2: Duplicated Metric Logic

**What people do:** Reimplement or lightly fork the same metric math in multiple training and evaluation paths.
**Why it's wrong:** Bugs diverge silently and benchmark numbers lose credibility.
**Do this instead:** Keep one tested metric implementation with narrow wrappers.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Yahoo Finance | Read-only market data fetch via loader helper | Cache or fixture this in tests rather than hitting live APIs |
| Binance | HTTP fetch plus SQLite persistence | Separate fetch logic from backtest orchestration |
| Hugging Face checkpoint registry | Model identifier passed into adapter | Record exact model metadata with outputs |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI <-> services | Direct function calls | Keep the boundary thin and explicit |
| Services <-> model adapter | Structured runtime parameters | Avoid scattering TimesFM-specific details |
| Backtest logic <-> persistence | Narrow write/read helpers | Makes schema changes safer |

## Sources

- `README.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONCERNS.md`

---
*Architecture research for: financial time-series forecasting toolkit*
*Researched: 2026-04-13*
