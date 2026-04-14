# Roadmap: TimesFM Finance Toolkit

## Overview

This roadmap hardens the existing repository into a trustworthy forecasting toolkit before any large platform migration or service expansion. The order is deliberate: establish a supported runtime story, enforce data and artifact contracts, fix trust-critical metrics under test, then improve performance and training reproducibility on top of that baseline.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions if needed later

- [x] **Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization** - Build the initial data foundation for storing, exploring, and organizing the project dataset. Completed 2026-04-13.
- [ ] **Phase 2: Create backtest architecture, qualification rules, and statistics collection** - Define the backtest structure, qualification criteria, and statistics pipeline needed for trustworthy evaluation.

## Phase Details

### Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization

**Goal:** Establish the first real data layer using PostgreSQL so the project can ingest, inspect, sort, and organize the datasets it will depend on.
**Requirements**: [DB-01, DB-02, DB-03, ING-01, ING-02, ING-03, DISC-01, DISC-02, DISC-03]
**Depends on:** Nothing (first phase)
**Success Criteria** (what must be TRUE):
  1. A PostgreSQL database is set up and reachable from the project runtime.
  2. The project can download or import the target datasets into the database in a repeatable way.
  3. The stored data can be explored, filtered, and sorted so the dataset structure is clear for later phases.
  4. The database schema and ingestion flow are documented well enough for Phase 1 planning.
**Plans:** 4 plans

Plans:
- [x] 01-01-PLAN.md - Compose-backed PostgreSQL foundation, schema bootstrap, and test harness
- [x] 01-02-PLAN.md - Idempotent Binance BTCUSDT ingestion with provenance tracking
- [x] 01-03-PLAN.md - Discovery, sorting, filtering, and integrity verification CLIs
- [x] 01-04-PLAN.md - PostgreSQL-to-CSV materialization bridge and Phase 1 docs

### Phase 2: Create backtest architecture, qualification rules, and statistics collection

**Goal:** Replace the SQLite-only crypto backtest experiment store with a PostgreSQL-backed architecture that persists run, window, and per-step prediction facts and exposes queryable per-horizon statistics using the locked Phase 2 metric semantics.
**Requirements**: [BT-01, BT-02, BT-03, BT-04, BT-05]
**Depends on:** Phase 1
**Success Criteria** (what must be TRUE):
  1. The backtest workflow writes canonical run, window, and per-step prediction facts to PostgreSQL through the shared repo connection path.
  2. PostgreSQL exposes direct per-step aggregate statistics for normalized deviation and overshoot/undershoot behavior across a run.
  3. Stored metrics and automated tests match the locked formulas and context-relative classification rules from Phase 2 context.
  4. The CLI wrapper and repository docs describe the PostgreSQL-backed backtest flow and no longer present SQLite as the canonical store.
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md - Metric semantics contract and reusable backtest metric module
- [x] 02-02-PLAN.md - PostgreSQL backtest schema, bootstrap, and query helpers
- [ ] 02-03-PLAN.md - Crypto backtest runtime migration, wrapper updates, and operator docs

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Set up PostgreSQL database, download and discover all data, add sorting and organization | 4/4 | Complete | 2026-04-13 |
| 2. Create backtest architecture, qualification rules, and statistics collection | 1/3 | In Progress | - |
