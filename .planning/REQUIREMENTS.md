# Requirements: TimesFM Finance Toolkit

**Defined:** 2026-04-13
**Core Value:** Users can run reproducible financial forecasting and backtesting workflows with the supported TimesFM finance checkpoint and clearly understand what is and is not supported.

## v1 Requirements

### Runtime

- [ ] **RUNT-01**: User can provision a supported inference or backtest environment from repository-provided artifacts without manual dependency discovery.
- [ ] **RUNT-02**: User can follow one current support matrix for forecast, evaluation, backtest, and training workflows and see clear guidance when a runtime is unsupported.

### Data Contracts

- [ ] **DATA-01**: User gets actionable validation errors when CSV or remote series inputs are missing required columns, out of order, too short, or otherwise unusable for forecasting.
- [ ] **DATA-02**: User can run forecast, evaluation, and backtest flows against one normalized series contract instead of each command enforcing different input assumptions.
- [ ] **DATA-03**: User can inspect model id, backend, and data-source metadata in generated forecast or backtest artifacts.

### Evaluation

- [ ] **EVAL-01**: User can trust directional metrics because neutral-threshold cases are counted correctly and covered by regression tests.
- [ ] **EVAL-02**: User can run rolling evaluation on supported workloads without one model invocation per forecast window.
- [ ] **EVAL-03**: User can run automated tests for forecast, evaluation, backtest, and metric helpers without depending on live Yahoo Finance or Binance calls.

### Safety

- [ ] **SAFE-01**: User can run the Dockerized crypto backtest path without giving the container unnecessary write access to the full repository.

### Training

- [ ] **TRNG-01**: User can provision a documented fine-tuning environment from repository artifacts instead of assembling the training stack ad hoc.
- [ ] **TRNG-02**: User can configure training runtime and model settings from checked-in configuration rather than hidden hard-coded entrypoint values.

## v2 Requirements

### Provenance and Scale

- **PROV-01**: User can pin exact model and dataset revisions automatically in output metadata.
- **SCALE-01**: User can orchestrate multi-symbol or multi-day benchmark jobs from one supported command.

### Platform Evolution

- **PLAT-01**: User can migrate the toolkit to a newer TimesFM API family behind compatibility tests.
- **SERV-01**: User can expose forecasts through a service or scheduled batch interface if the product direction expands beyond CLI use.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Direct trade execution | The repository's current value is forecasting and evaluation, not brokerage automation |
| Hosted web product | No service architecture, auth model, or deployment target exists today |
| Native Windows support for the full model stack | The documented and practical runtime path remains Docker, WSL, or Linux |
| Publication of the proprietary fine-tuning dataset | The source dataset is not available for distribution from this repo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RUNT-01 | Phase 1 | Pending |
| RUNT-02 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| EVAL-01 | Phase 3 | Pending |
| EVAL-02 | Phase 4 | Pending |
| EVAL-03 | Phase 3 | Pending |
| SAFE-01 | Phase 4 | Pending |
| TRNG-01 | Phase 5 | Pending |
| TRNG-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initial definition*
