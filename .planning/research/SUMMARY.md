# Project Research Summary

**Project:** TimesFM Finance Toolkit
**Domain:** Financial time-series forecasting and backtesting toolkit
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Executive Summary

This repository is already more than a research scratchpad: it has working CLI flows for forecasting, rolling evaluation, and crypto minute backtesting. The main research conclusion is that the next milestone should not chase broad new product surface. It should harden the existing toolkit so users can trust the runtime setup, inputs, outputs, and benchmark results.

The recommended approach is to keep the current TimesFM v1 platform target, formalize one supported runtime story, centralize validation and metrics, and add the missing automated test harness before larger migrations. The biggest risks are not feature gaps; they are trust gaps: incorrect metrics, brittle environments, monolithic runtime code, and unclear operational boundaries.

## Key Findings

### Recommended Stack

Keep Python 3.10, the current TimesFM v1 compatibility layer, pandas/NumPy, and Docker as the main operational stack. Add a real automated test runner and treat Docker or Linux-like environments as the supported execution boundary for the model runtime.

**Core technologies:**
- Python 3.10: current repo runtime and compatibility floor
- TimesFM 1.3.0 / legacy checkpoint family: current model contract to stabilize
- Pandas and NumPy: existing series and metrics foundation
- Docker: reproducible execution path, especially for Windows-hosted use

### Expected Features

The table stakes for this repository are reproducible runtime setup, strong input validation, trusted metrics, test coverage, and output provenance. The differentiators are the finance-tuned checkpoint path and the SQLite-backed crypto backtest workflow. Hosted services, direct trading automation, and immediate platform migration should be deferred.

**Must have (table stakes):**
- Supported runtime bootstrap and smoke-checked command paths
- Shared input validation and output provenance
- Correct metrics plus automated regression tests

**Should have (competitive):**
- Hardened crypto minute backtest history
- Config-driven fine-tuning workflow

**Defer (v2+):**
- Hosted services and orchestration
- Migration to a newer TimesFM API family

### Architecture Approach

Use thin CLI entrypoints over a shared service layer for data loading, model adaptation, metric math, and persistence. The roadmap should first stabilize the execution boundary and only then split the more fragile runtime files behind cleaner internal seams.

**Major components:**
1. CLI entrypoints - forecast, evaluation, backtest, and training commands
2. Shared runtime services - validation, data loading, model setup, metrics, persistence
3. Artifact layer - CSV outputs, SQLite history, logs, and checkpoints

### Critical Pitfalls

1. **Invalid market data reaches model math** - prevent with one explicit input contract
2. **Metric drift makes benchmarks untrustworthy** - prevent with shared math and regression fixtures
3. **Supported runtime docs drift from reality** - prevent with a support matrix and smoke runs
4. **Backtest runtime stays monolithic** - prevent by separating concerns before expansion
5. **Docker write boundaries stay too broad** - prevent with safer mount rules

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Runtime Baseline
**Rationale:** A supported runtime story is the foundation for every later fix.
**Delivers:** Reproducible setup, support matrix, and smoke-checked command entrypoints.
**Addresses:** Supported runtime bootstrap.
**Avoids:** Documentation and runtime drift.

### Phase 2: Data Contracts and Provenance
**Rationale:** Validation and provenance should be fixed before benchmarking or refactoring performance.
**Delivers:** Shared input validation and richer output metadata.
**Uses:** Existing loader paths and artifact writers.
**Implements:** Input boundary and artifact contract cleanup.

### Phase 3: Metrics and Test Harness
**Rationale:** Trustworthy numbers are mandatory before optimization work.
**Delivers:** Metric correctness fixes and automated regression coverage.
**Uses:** Shared metric layer and fixture-based tests.
**Implements:** The main benchmark credibility guardrail.

### Phase 4: Backtest Performance and Safety
**Rationale:** Once behavior is trustworthy, performance and container safety can be improved without guessing.
**Delivers:** Batched rolling evaluation and safer Docker-backed backtest operations.
**Uses:** The validation and test harness established earlier.

### Phase 5: Training Reproducibility
**Rationale:** The training path is important but should be hardened after the inference surface is stable.
**Delivers:** Reproducible environment specs and config-driven training runtime settings.
**Uses:** The same trust-first framing applied to the research workflow.

### Phase Ordering Rationale

- Runtime support comes first because every other phase depends on a fresh environment being reproducible.
- Validation precedes metric fixes because bad inputs can invalidate benchmark conclusions.
- Tests precede optimization so performance changes do not move correctness regressions into production.
- Training reproducibility is separated from inference hardening to avoid mixing platform migration with user-facing trust work.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4:** batching changes and Docker write-boundary changes need careful integration choices
- **Phase 5:** the full training dependency story may still require targeted environment research

Phases with standard patterns (skip research-phase if desired):
- **Phase 1:** support matrix and smoke validation are standard hardening work
- **Phase 2:** input contracts and provenance stamping follow established CLI-toolkit patterns
- **Phase 3:** shared metric fixes and regression tests are standard reliability work

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Driven directly by repo docs and codebase analysis |
| Features | MEDIUM | Inferred from repo purpose and current gap profile |
| Architecture | MEDIUM | Strong evidence from the codebase, but some refactor seams are still inferred |
| Pitfalls | HIGH | Directly supported by the existing concerns audit |

**Overall confidence:** MEDIUM

### Gaps to Address

- Training environment pinning details may need more targeted planning before implementation.
- Exact provenance fields for CSV and SQLite outputs should be decided during phase planning, not assumed globally here.

## Sources

### Primary (HIGH confidence)
- `README.md` - runtime story and supported commands
- `.planning/codebase/ARCHITECTURE.md` - current system shape
- `.planning/codebase/CONCERNS.md` - known gaps and risks

### Secondary (MEDIUM confidence)
- `.planning/codebase/STACK.md` - current dependency and platform analysis
- `.planning/codebase/STRUCTURE.md` - module organization context

---
*Research completed: 2026-04-13*
*Ready for roadmap: yes*
