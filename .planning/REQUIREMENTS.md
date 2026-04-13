# Requirements: TimesFM Finance Toolkit

**Defined:** 2026-04-13
**Core Value:** Users can run reproducible financial forecasting and backtesting workflows with the supported TimesFM finance checkpoint and clearly understand what is and is not supported.

## v1 Requirements

### Database

- [x] **DB-01**: User can provision a PostgreSQL database and connect to it from the project runtime with one documented setup path.
- [x] **DB-02**: User can create the required PostgreSQL schema for assets, observations, and dataset metadata without manual ad hoc SQL edits.
- [x] **DB-03**: User can store financial time-series data in PostgreSQL with enough structure to query by symbol, source, timeframe, and date range.

### Ingestion

- [x] **ING-01**: User can download or import the target market data into PostgreSQL through a repeatable project command or script.
- [x] **ING-02**: User can rerun ingestion without creating duplicate rows or silently corrupting existing data.
- [x] **ING-03**: User can track where imported data came from, when it was loaded, and what date range it covers.

### Discovery And Organization

- [x] **DISC-01**: User can inspect which symbols, sources, and date ranges are currently available in the PostgreSQL dataset.
- [x] **DISC-02**: User can sort and filter stored data by symbol, source, timeframe, and date so the dataset is easy to explore.
- [x] **DISC-03**: User can understand the database schema and ingestion workflow from repository documentation without reverse-engineering the code.

## v2 Requirements

### Modeling On Top Of PostgreSQL

- **MODEL-01**: User can drive forecasting or evaluation workflows directly from PostgreSQL-backed datasets instead of ad hoc file inputs.
- **MODEL-02**: User can materialize model-ready training or inference datasets from the PostgreSQL store with consistent selection rules.

### Operations

- **OPS-01**: User can schedule recurring data refreshes into PostgreSQL.
- **OPS-02**: User can expose dataset summaries through a lightweight API or dashboard if needed later.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Direct trade execution | The current scope is data foundation and later modeling, not brokerage automation |
| Full hosted product or dashboard in v1 | The immediate goal is PostgreSQL-backed data setup and exploration, not a user-facing service |
| Real-time streaming ingestion in v1 | A reliable batch ingestion foundation should exist before live pipelines |
| Publication of the proprietary fine-tuning dataset | The source dataset is not available for distribution from this repo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DB-01 | Phase 1 | Satisfied |
| DB-02 | Phase 1 | Satisfied |
| DB-03 | Phase 1 | Satisfied |
| ING-01 | Phase 1 | Satisfied |
| ING-02 | Phase 1 | Satisfied |
| ING-03 | Phase 1 | Satisfied |
| DISC-01 | Phase 1 | Satisfied |
| DISC-02 | Phase 1 | Satisfied |
| DISC-03 | Phase 1 | Satisfied |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after Phase 1 verification*
