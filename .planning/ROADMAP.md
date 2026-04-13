# Roadmap: TimesFM Finance Toolkit

## Overview

This roadmap hardens the existing repository into a trustworthy forecasting toolkit before any large platform migration or service expansion. The order is deliberate: establish a supported runtime story, enforce data and artifact contracts, fix trust-critical metrics under test, then improve performance and training reproducibility on top of that baseline.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions if needed later

- [ ] **Phase 1: Supported Runtime Baseline** - Define and enforce the supported environment story for existing command paths.
- [ ] **Phase 2: Data Contracts and Provenance** - Normalize input validation and stamp outputs with runtime metadata.
- [ ] **Phase 3: Metrics and Test Harness** - Fix trust-critical metric behavior and add automated regression coverage.
- [ ] **Phase 4: Backtest Performance and Container Safety** - Improve evaluation throughput and tighten Docker write boundaries.
- [ ] **Phase 5: Training Reproducibility** - Make the fine-tuning path reproducible and config-driven.

## Phase Details

### Phase 1: Supported Runtime Baseline
**Goal**: Establish one supported runtime matrix and reproducible smoke path for forecast, evaluation, backtest, and training entrypoints.
**Depends on**: Nothing (first phase)
**Requirements**: [RUNT-01, RUNT-02]
**Success Criteria** (what must be TRUE):
  1. A fresh user can provision a supported inference or backtest runtime from repository artifacts and complete a documented smoke run.
  2. Supported and unsupported runtime combinations are documented in one current support matrix.
  3. Unsupported runtime choices fail with clear guidance instead of deep dependency errors.
**Plans**: 2 plans

Plans:
- [ ] 01-01: Normalize runtime bootstrap artifacts and support matrix
- [ ] 01-02: Add smoke validation for documented command paths

### Phase 2: Data Contracts and Provenance
**Goal**: Create one explicit input contract for market data and record the metadata needed to trust generated artifacts.
**Depends on**: Phase 1
**Requirements**: [DATA-01, DATA-02, DATA-03]
**Success Criteria** (what must be TRUE):
  1. Forecast, evaluation, and backtest commands reject malformed or too-short inputs with actionable errors.
  2. Shared loader behavior removes drift between command-specific input assumptions.
  3. Forecast and backtest artifacts capture model, backend, and data-source provenance.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Define and implement the shared series input contract
- [ ] 02-02: Route forecast, evaluation, and backtest loaders through the shared contract
- [ ] 02-03: Add provenance fields to generated artifacts

### Phase 3: Metrics and Test Harness
**Goal**: Make benchmark outputs trustworthy by fixing metric correctness issues and adding deterministic regression tests.
**Depends on**: Phase 2
**Requirements**: [EVAL-01, EVAL-03]
**Success Criteria** (what must be TRUE):
  1. Directional metrics handle neutral-threshold cases correctly and sample counts reconcile.
  2. Automated tests cover metric helpers plus the core forecast, evaluation, and backtest command paths.
  3. Test runs do not depend on live Yahoo Finance or Binance responses.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Consolidate and fix metric correctness for directional evaluation
- [ ] 03-02: Add fixture-driven tests for loaders and metrics
- [ ] 03-03: Add command-path regression coverage with mocked external dependencies

### Phase 4: Backtest Performance and Container Safety
**Goal**: Improve repeated evaluation/backtest usability while reducing operational risk from the Docker execution path.
**Depends on**: Phase 3
**Requirements**: [EVAL-02, SAFE-01]
**Success Criteria** (what must be TRUE):
  1. Rolling evaluation avoids one forecast call per window for supported workloads.
  2. The Docker-backed backtest path no longer requires unnecessary write access to the full repository.
  3. Backtest changes can be tested through narrower seams than the current monolithic runtime file.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Batch rolling evaluation and isolate backtest performance seams
- [ ] 04-02: Tighten Docker mount boundaries and document the container trust model

### Phase 5: Training Reproducibility
**Goal**: Turn the fine-tuning path into a documented, configurable workflow rather than a fragile experiment harness.
**Depends on**: Phase 4
**Requirements**: [TRNG-01, TRNG-02]
**Success Criteria** (what must be TRUE):
  1. The training environment can be provisioned from repository artifacts without guesswork.
  2. Training runtime and model settings come from checked-in configuration instead of hidden entrypoint constants.
  3. The documented training flow matches what the code actually supports.
**Plans**: 3 plans

Plans:
- [ ] 05-01: Add a reproducible training environment spec
- [ ] 05-02: Move runtime and model settings into checked-in configuration
- [ ] 05-03: Align training docs and validation with the supported workflow

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Supported Runtime Baseline | 0/2 | Not started | - |
| 2. Data Contracts and Provenance | 0/3 | Not started | - |
| 3. Metrics and Test Harness | 0/3 | Not started | - |
| 4. Backtest Performance and Container Safety | 0/2 | Not started | - |
| 5. Training Reproducibility | 0/3 | Not started | - |
