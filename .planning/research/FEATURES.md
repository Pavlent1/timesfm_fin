# Feature Research

**Domain:** Financial time-series forecasting and backtesting toolkit
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Supported runtime bootstrap | Users expect to install and run the documented command paths without guessing dependencies | MEDIUM | The repo currently documents part of this for inference but not for training |
| Forecast input validation | Users expect bad CSVs or short series to fail clearly before model execution | MEDIUM | Especially important because finance data quality is noisy and user supplied |
| Reproducible metrics | Users expect benchmark numbers to mean what they say | MEDIUM | The current directional-metric bug makes this a must-fix trust issue |
| Automated regression tests | Users expect changes to not silently break CLIs and math | MEDIUM | Missing entirely in the current repo |
| Output provenance | Users expect outputs to show what model, backend, and data source produced them | LOW | Critical when comparing runs across local, Docker, and remote data sources |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Crypto minute backtest with SQLite history | Gives the repo a concrete experiment loop instead of a toy one-shot forecast demo | MEDIUM | Already present, but needs hardening and safer operations |
| Finance-tuned TimesFM checkpoint support | The repo is specialized for financial data rather than generic forecasting | HIGH | This is the core domain differentiator and should stay central |
| Config-driven fine-tuning workflow | Makes the research path reproducible instead of one-off | HIGH | Valuable because the current training path is hard to reproduce |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Hosted real-time trading service | It sounds like the natural next step from forecasting | It explodes scope into auth, infrastructure, latency, and brokerage risk that the repo does not currently support | Keep the project as an offline research and evaluation toolkit |
| Native Windows GPU support for the full stack | Windows users want a one-command local path | The current JAX/PAX dependency story is not reliable there | Keep Docker/WSL as the documented support boundary |
| Immediate TimesFM API migration during stabilization | Newer APIs feel more future-proof | It mixes platform migration risk with reliability work and removes a stable baseline | Stabilize the current v1 contract first, then migrate behind tests |

## Feature Dependencies

```text
Supported runtime bootstrap
    --> enables --> forecast / evaluation / backtest smoke validation

Forecast input validation
    --> supports --> reproducible metrics
    --> supports --> safer backtest persistence

Automated regression tests
    --> protects --> metric fixes
    --> protects --> training config cleanup

Output provenance
    --> enhances --> benchmark comparison
    --> enhances --> debugging across Docker and local runs
```

### Dependency Notes

- **Runtime bootstrap requires a supported environment spec:** without that, every downstream CLI remains fragile.
- **Validation supports metrics:** incorrect or malformed inputs can make correct metric code look broken.
- **Tests protect refactors:** performance and training cleanup should not proceed without a harness.

## MVP Definition

### Launch With (v1)

- [ ] Supported runtime bootstrap for inference, evaluation, and backtest flows - essential to make the repo usable without tribal knowledge
- [ ] Clear input validation and output provenance - essential for trustworthy experiments
- [ ] Correct directional metrics plus automated regression coverage - essential for credible benchmark results
- [ ] Safer and faster crypto/evaluation workflows - essential for day-to-day use
- [ ] Reproducible fine-tuning setup and config wiring - essential to keep the training path real rather than aspirational

### Add After Validation (v1.x)

- [ ] Checkpoint and dataset revision pinning - add once the baseline workflow is stable
- [ ] Multi-symbol or multi-day orchestration commands - add once single-run paths are trustworthy

### Future Consideration (v2+)

- [ ] Hosted API or scheduled batch service - defer until there is a clear operational product direction
- [ ] Migration to a newer TimesFM API family - defer until current behavior is covered by tests

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Supported runtime bootstrap | HIGH | MEDIUM | P1 |
| Forecast input validation | HIGH | MEDIUM | P1 |
| Output provenance | MEDIUM | LOW | P1 |
| Correct directional metrics | HIGH | MEDIUM | P1 |
| Automated regression tests | HIGH | MEDIUM | P1 |
| Batched rolling evaluation | MEDIUM | MEDIUM | P2 |
| Safer Docker write boundary | MEDIUM | LOW | P2 |
| Config-driven fine-tuning | HIGH | HIGH | P1 |

## Competitor Feature Analysis

| Feature | Generic research repo | Packaged forecasting CLI | Our Approach |
|---------|-----------------------|--------------------------|--------------|
| Runtime setup | Often under-documented | Usually scripted and reproducible | Move this repo toward the packaged CLI standard without losing research flexibility |
| Metrics trust | Often ad hoc | Usually expected to be tested | Prioritize correctness and regression tests before feature expansion |
| Experiment persistence | Often notebook-local | Often saved in structured outputs | Keep SQLite history for backtests as a differentiator |

## Sources

- `README.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `.planning/codebase/STACK.md`

---
*Feature research for: financial time-series forecasting toolkit*
*Researched: 2026-04-13*
