# Pitfalls Research

**Domain:** Financial time-series forecasting and backtesting toolkit
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Invalid market data reaches model math

**What goes wrong:**
Malformed dates, missing target values, too-short histories, or nonpositive prices pass through loaders and fail later in confusing ways.

**Why it happens:**
Research code often validates only the happy path and assumes pre-cleaned datasets.

**How to avoid:**
Define one shared input contract and validate it before any forecasting, evaluation, or training logic runs.

**Warning signs:**
Users see runtime stack traces instead of actionable input errors, or metric runs produce NaNs without clear cause.

**Phase to address:**
Phase 2

---

### Pitfall 2: Metric drift makes benchmarks untrustworthy

**What goes wrong:**
Directional and accuracy-style metrics disagree across scripts or silently drop edge cases.

**Why it happens:**
Metric logic is duplicated across multiple code paths without tests.

**How to avoid:**
Consolidate metric math, add regression fixtures for neutral-band cases, and make benchmark scripts depend on the shared implementation.

**Warning signs:**
Different scripts report incompatible numbers for the same series, or confusion-matrix totals do not match sample counts.

**Phase to address:**
Phase 3

---

### Pitfall 3: Supported runtime story diverges from repo docs

**What goes wrong:**
Commands in the README or scripts no longer match what the code actually supports.

**Why it happens:**
The repo mixes a stabilized inference path with a still-research-grade training path, but they are documented together.

**How to avoid:**
Maintain a support matrix, keep smoke commands under test, and make unsupported paths fail with explicit guidance.

**Warning signs:**
Fresh environment setup requires manual dependency discovery, or helpers behave differently than the README claims.

**Phase to address:**
Phase 1

---

### Pitfall 4: The backtest path becomes impossible to change safely

**What goes wrong:**
Small updates to fetch logic, schema, or metrics break unrelated backtest behaviors.

**Why it happens:**
`src/crypto_minute_backtest.py` owns too many responsibilities in one file.

**How to avoid:**
Create cleaner seams between ingestion, forecasting, metrics, and persistence before expanding the feature.

**Warning signs:**
A schema tweak forces unrelated forecast logic changes, or tests cannot isolate failures by concern.

**Phase to address:**
Phase 4

---

### Pitfall 5: Dockerized runs can mutate the repository unexpectedly

**What goes wrong:**
Container execution has write access to the entire checkout and can change source or planning files.

**Why it happens:**
The current wrapper mounts the full repo read-write for convenience.

**How to avoid:**
Restrict writable mounts to outputs or use read-only source mounts wherever possible.

**Warning signs:**
Source files change after a backtest run or it becomes hard to reason about container trust boundaries.

**Phase to address:**
Phase 4

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hard-coding runtime settings in entrypoints | Faster experiments | Config drift and irreproducible runs | Only for one-off local debugging, not committed workflows |
| Duplicating helper logic across training and evaluation | Faster short-term implementation | Bug fixes do not propagate consistently | Never once multiple user-facing paths depend on the logic |
| Using live APIs during validation | Easy manual realism | Flaky tests and rate-limit failures | Manual smoke runs only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Yahoo Finance | Treating download success as data validity | Validate columns, order, nulls, and history length after download |
| Binance | Combining fetch, persistence, and evaluation state in one function | Keep fetch, schema, and backtest orchestration separated |
| Hugging Face checkpoint ids | Treating model id alone as enough provenance | Record model id, backend, and relevant runtime metadata in outputs |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| One forecast call per rolling window | Slow evaluation loops and poor multi-ticker scaling | Batch contexts for supported workloads | As soon as users benchmark more than one short series |
| Repeated full-frame preprocessing copies | High memory overhead in training and evaluation | Move validation and reshaping into tighter helpers or streaming-friendly paths | Larger datasets and longer training runs |
| SQLite plus monolithic orchestration | Hard-to-debug slowdowns in backtests | Separate persistence from compute and keep schema helpers narrow | When backtests expand beyond one-day experiments |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Trusting arbitrary remote model ids without provenance | Unclear runtime behavior and reproducibility gaps | Record model source metadata and constrain supported ids where appropriate |
| Mounting the full repo read-write into Docker | Accidental or malicious source mutation | Prefer outputs-only writable mounts or read-only source mounts |
| Treating public market data as inherently clean | Silent bad-input propagation into metrics or forecasts | Validate all external inputs as if they were user supplied |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Unsupported platforms fail deep in dependency setup | Users think the repo is broken | Fail fast with a support matrix and clear runtime guidance |
| CLI flags differ subtly between workflows | Users cannot move from forecast to evaluation or backtest confidently | Normalize option contracts and naming where possible |
| Outputs lack model/runtime metadata | Users cannot compare or trust runs later | Stamp outputs with provenance fields |

## "Looks Done But Isn't" Checklist

- [ ] **Forecast CLI:** verifies malformed CSVs and too-short series with clear errors, not raw stack traces
- [ ] **Metrics fix:** includes neutral-band regression coverage and sample-count sanity checks
- [ ] **Docker wrapper:** documents and enforces the intended write boundary
- [ ] **Training setup:** can be recreated from repository artifacts instead of oral history

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Invalid data reached the model | LOW | Add validation, capture failing fixture, and rerun the command path |
| Metric drift shipped | MEDIUM | Centralize the math, add regression tests, and re-baseline published numbers |
| Runtime docs drifted | MEDIUM | Rebuild the environment from scratch, update support docs, and add a smoke test |
| Backtest monolith regressed | HIGH | Split responsibilities, add seam-level tests, and re-run representative backtests |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Invalid market data reaches model math | Phase 2 | Fixture and CLI tests reject malformed inputs early |
| Metric drift makes benchmarks untrustworthy | Phase 3 | Regression fixtures and benchmark smoke tests stay green |
| Supported runtime story diverges from docs | Phase 1 | Fresh environment smoke run matches documented commands |
| Backtest path becomes unsafe to change | Phase 4 | Separated helpers and focused tests cover fetch, metrics, and persistence |
| Dockerized runs mutate the repo unexpectedly | Phase 4 | Container run writes only to allowed output locations |

## Sources

- `.planning/codebase/CONCERNS.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STACK.md`
- `README.md`

---
*Pitfalls research for: financial time-series forecasting toolkit*
*Researched: 2026-04-13*
