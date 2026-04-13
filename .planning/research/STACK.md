# Stack Research

**Domain:** Financial time-series forecasting and backtesting toolkit
**Researched:** 2026-04-13
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10 | Primary runtime for all repo workflows | Matches the current repository, the TimesFM compatibility constraints, and the existing Docker/bootstrap story |
| TimesFM | 1.3.0 / v1 checkpoint family | Forecasting model runtime for inference and fine-tuning | The repository already targets the legacy finance checkpoint family and should stabilize that path before attempting migration |
| Pandas + NumPy | 2.2.x / 1.26.x | Series loading, shaping, metrics, and output formatting | They are already used throughout the repo and remain the practical baseline for finance-oriented CLI workflows |
| Docker | Current engine runtime | Reproducible execution path for Windows-hosted users and backtest runs | The repo already documents Docker as the supported Windows path for the model runtime |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| JAX + PaxML/Praxis | Legacy stack already in repo | Fine-tuning and checkpoint evaluation | Only for the training/evaluation path that depends on the current TimesFM v1 implementation |
| yfinance | 0.2.x | Pull public equity price history for forecast/evaluation demos | Use for Yahoo-backed CLIs and lightweight smoke runs |
| sqlite3 | Python stdlib | Persist backtest runs, candles, and per-window predictions | Use for local experiment tracking in the crypto backtest path |
| pytest | Add in v1 hardening work | Automated regression coverage for loaders, metrics, and CLIs | Use to replace the current no-tests state with deterministic local validation |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| PowerShell wrappers | Windows setup and Docker orchestration | Keep wrappers thin and move behavior into Python where possible |
| Dockerfile | Reproducible inference and backtest runtime | Prefer mounting outputs writable and source read-only when feasible |
| GSD planning docs | Phase planning and execution tracking | Useful here because the repo has multiple reliability gaps rather than one isolated feature gap |

## Installation

```bash
# Inference and backtest runtime
python -m venv .venv
pip install "timesfm[pax]==1.3.0"
pip install -r requirements.inference.txt

# Recommended hardening addition
pip install pytest

# Container path
docker build -t timesfm-fin .
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Docker-first runtime support on Windows | Native Windows JAX/PAX support | Only if the model stack becomes officially supportable on Windows without the current dependency wall |
| Legacy TimesFM v1 compatibility as the active target | Immediate migration to newer TimesFM APIs | Only after the current repo behavior is stabilized and covered by tests |
| SQLite experiment persistence | Ad hoc CSV-only result storage | Only for one-off local debugging where relational history is unnecessary |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Treating native Windows as the primary supported model runtime | The current checkpoint path still depends on Linux-like execution assumptions | Docker, WSL, or Linux |
| Unpinned or undocumented training dependency assembly | The repo already shows that this creates onboarding and reproducibility gaps | A checked-in training environment spec |
| Live remote APIs in automated tests | They create flaky tests and slow feedback loops | Fixture CSVs and mocked HTTP/model boundaries |

## Stack Patterns by Variant

**If the goal is inference, evaluation, or backtesting:**
- Use the lightweight CLI path around `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`
- Because that is the clearest supported product surface already present in the repository

**If the goal is fine-tuning:**
- Keep the current JAX/PAX stack but move runtime settings into checked-in config and environment specs
- Because the code already exists, but the operational contract is still missing

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `timesfm==1.3.0` | Python 3.10 | This is the explicit compatibility target documented in the repo |
| JAX/PAX training code | Legacy TimesFM v1 internals | The training path is tightly coupled to the older upstream APIs |
| Docker image | Repo CLI entrypoints | The current image is the most practical Windows-hosted execution path |

## Sources

- `README.md` - supported runtime story, model version, and documented entrypoints
- `.planning/codebase/STACK.md` - current repository stack analysis
- `.planning/codebase/ARCHITECTURE.md` - runtime split between training and inference paths
- `.planning/codebase/CONCERNS.md` - operational and reproducibility gaps that shape the recommended stack

---
*Stack research for: financial time-series forecasting toolkit*
*Researched: 2026-04-13*
