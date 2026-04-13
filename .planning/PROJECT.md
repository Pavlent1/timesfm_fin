# TimesFM Finance Toolkit

## What This Is

This repository is a brownfield Python toolkit for fine-tuning and running the legacy TimesFM v1 model on financial time-series data. It currently serves researchers and engineers who need CLI-driven forecasting, rolling evaluation, and crypto minute backtesting without turning the project into a hosted trading service.

## Core Value

Users can run reproducible financial forecasting and backtesting workflows with the supported TimesFM finance checkpoint and clearly understand what is and is not supported.

## Requirements

### Validated

- [x] Run a single-series forecast from Yahoo Finance or a local CSV and optionally write predictions to CSV.
- [x] Run rolling evaluation over one or more series and report forecast error plus directional metrics.
- [x] Execute a BTCUSDT 1-minute backtest or live forecast flow with SQLite persistence for runs and per-window predictions.
- [x] Launch a research-oriented fine-tuning or checkpoint evaluation flow against a local financial dataset using the TimesFM v1 stack.
- [x] Establish a PostgreSQL-backed data foundation for financial datasets. Validated in Phase 1.
- [x] Download or import the target datasets into PostgreSQL through repeatable project workflows. Validated in Phase 1.
- [x] Make stored data easy to discover, sort, and filter by symbol, source, timeframe, and date range. Validated in Phase 1.
- [x] Document the schema and ingestion flow so later modeling phases build on a clear data layer. Validated in Phase 1.

### Active

- [ ] Evaluate which later workflows should read PostgreSQL directly instead of consuming CSV materializations.
- [ ] Decide how recurring refreshes or scheduled PostgreSQL ingestion should work once the batch foundation is stable.

### Out of Scope

- Hosted prediction APIs or always-on services - the repository is a batch/CLI toolkit today.
- Direct brokerage execution or automated trading - the project focuses on forecasting and evaluation, not order routing.
- Native Windows support for the full JAX/PAX checkpoint stack - Docker, Linux, or WSL remain the supported runtime story.
- Publishing the proprietary fine-tuning dataset - the repo documents public data sources but cannot ship the original training corpus.

## Context

The repository mixes two product shapes: an older research-grade fine-tuning path built around JAX, PaxML, and Praxis, and a newer CLI-oriented inference path for forecasts, rolling evaluation, and crypto minute backtests. The codebase map shows that the inference path is the clearest supported user journey today, while the training path still depends on manually assembled environments and hard-coded runtime settings.

Recent repository work already moved part of the project toward a more usable toolkit by adding `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, Docker support, and Windows helper scripts. The remaining gaps are mostly productization gaps: environment reproducibility, consistent data contracts, trustworthy metrics, automated verification, and clearer operational boundaries.

The current codebase also carries known risks that should shape planning: duplicated metric logic, a monolithic crypto backtest file, remote model/data inputs without provenance controls, and missing automated tests across the main CLI flows. Those gaps matter because this repository's value depends more on trustworthy execution than on adding broad new feature surface.

## Current State

Phase 1 is complete. The repo now has a Docker-managed PostgreSQL data layer with checked-in schema bootstrap, repeatable Binance ingestion, dataset discovery and integrity CLIs, and CSV materialization back into the existing forecasting and training flows.

## Constraints

- **Tech stack**: Python 3.10 plus the legacy TimesFM v1 / JAX / PAX ecosystem - the repository is intentionally aligned to the older checkpoint family.
- **Runtime**: Linux, WSL, or Docker for the supported checkpoint path - native Windows remains an orchestration environment rather than the target runtime.
- **Data**: Fine-tuning depends on private financial datasets - public examples must rely on Yahoo Finance, Binance, or user-provided CSV files.
- **Product shape**: CLI-first workflows only - there is no current web app, background service, or deployment target to build against.
- **Trust boundary**: Remote checkpoints and market data are fetched from external services - reproducibility and provenance need to be made explicit in outputs and docs.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep TimesFM v1 compatibility as the current platform target | The repository, README, and checkpoint support are all anchored to the legacy TimesFM finance checkpoint family | Pending |
| Treat this as a brownfield hardening effort, not a greenfield redesign | The repo already has working forecast, evaluation, and backtest paths that should be stabilized before larger migrations | Pending |
| Keep Docker as the primary supported Windows execution path | The documented Windows story already depends on containerized or Linux-like execution for the model runtime | Validated in Phase 1 via Compose-managed PostgreSQL setup and docs |
| Prioritize trust and reproducibility over adding novel product features | The biggest current risks are incorrect metrics, unsupported environments, and unverified workflows | Validated in Phase 1 via provenance tracking, integrity checks, and automated tests |
| Start the new roadmap with a PostgreSQL-backed data foundation | Later modeling work depends on having discoverable, organized, queryable historical data | Validated in Phase 1 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after Phase 1 completion*
