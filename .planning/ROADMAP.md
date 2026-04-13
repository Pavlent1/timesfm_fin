# Roadmap: TimesFM Finance Toolkit

## Overview

This roadmap hardens the existing repository into a trustworthy forecasting toolkit before any large platform migration or service expansion. The order is deliberate: establish a supported runtime story, enforce data and artifact contracts, fix trust-critical metrics under test, then improve performance and training reproducibility on top of that baseline.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions if needed later

- [ ] **Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization** - Build the initial data foundation for storing, exploring, and organizing the project dataset.

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
- [ ] 01-01-PLAN.md - Compose-backed PostgreSQL foundation, schema bootstrap, and test harness
- [ ] 01-02-PLAN.md - Idempotent Binance BTCUSDT ingestion with provenance tracking
- [ ] 01-03-PLAN.md - Discovery, sorting, filtering, and integrity verification CLIs
- [ ] 01-04-PLAN.md - PostgreSQL-to-CSV materialization bridge and Phase 1 docs

## Progress

**Execution Order:**
Phases execute in numeric order: 1

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Set up PostgreSQL database, download and discover all data, add sorting and organization | 0/4 | Planned | - |
