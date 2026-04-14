# Test Audit

- Date: 2026-04-13
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Audit mode: repo inspection plus real command execution
- Preferences status: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` is still `draft`, so the audit used conservative defaults

## Commands Run

- `node scripts/testing/discover-test-landscape.mjs --markdown`
- `node scripts/testing/measure-coverage.mjs --markdown`
- `node scripts/testing/summarize-test-gaps.mjs --markdown`
- `node scripts/precommit-checks.mjs`
- `python -m pytest --collect-only -q`
- `python -m pytest tests/test_docs_contract.py -q`
- `.\.venv\Scripts\python.exe -m pytest --version`
- `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_docs_contract.py -q`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Severity-Ordered Findings

### 1. Broken Or Non-Functional Test Execution: most of the suite is currently blocked by shared Docker startup

- Evidence:
  - `.\.venv\Scripts\python.exe -m pytest -q` collected 12 tests but ended with `2 passed, 10 errors`
  - every failing test died in the shared session fixture in `tests/conftest.py:35-52`
  - the failure occurs before assertions run because `docker compose up -d postgres` cannot reach Docker on this machine
  - the repo-managed gate in `scripts/precommit-checks.mjs:83-103` also exits before running pytest when Docker is unavailable
- Classification: broken or non-functional test execution
- Impact:
  - most test signal is unavailable in environments where Docker is not ready
  - one infrastructure failure masks all database-backed behavior, so application regressions are indistinguishable from environment outages

### 2. Missing Runnable Audit Tooling: required discovery, coverage, and gap scripts do not exist

- Evidence:
  - `node scripts/testing/discover-test-landscape.mjs --markdown` failed with `MODULE_NOT_FOUND`
  - `node scripts/testing/measure-coverage.mjs --markdown` failed with `MODULE_NOT_FOUND`
  - `node scripts/testing/summarize-test-gaps.mjs --markdown` failed with `MODULE_NOT_FOUND`
- Classification: missing runnable command and missing coverage measurement
- Impact:
  - there is no repo-owned automated way to inventory the test landscape, measure coverage, or summarize hotspots
  - future planning work must start from manual inspection instead of durable automation

### 3. Fragile Layering: almost all existing tests are integration tests gated by the same Docker-backed fixture

- Evidence:
  - 10 of 12 collected tests require the `repo_postgres_service` fixture in `tests/conftest.py:35-52`
  - the only isolated passing tests during this audit were `test_load_postgres_settings_uses_repo_defaults` and `test_readme_and_db_readme_document_phase1_postgres_workflow`
- Classification: fragile pattern and incorrect layer balance
- Impact:
  - pure logic inside the PostgreSQL data pipeline has very little protection when Docker is unavailable
  - a single environment dependency turns the suite into an all-or-nothing check instead of a layered safety net

### 4. Important Shared Adapters And CLIs Have No Direct Tests

- Evidence:
  - `src/binance_market_data.py:25-78` contains pagination, de-duplication, stalled-cursor protection, and HTTP 429 retry logic with no direct automated tests detected
  - `src/bootstrap_postgres.py:16-78` contains CLI parsing, readiness waiting, and schema application flow with no direct automated tests detected
- Classification: missing tests for important behavior
- Impact:
  - failures in shared network-fetch logic would likely surface late through larger workflows
  - bootstrap CLI regressions can slip through even though the Postgres path is currently a major focus of the tested area

### 5. Core Forecasting, Backtesting, And Training Surfaces Remain Untested

- Evidence:
  - no direct tests were found for `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/mock_trading.py`, `src/mock_trading_utils.py`, `configs/fine_tuning.py`, `scripts/setup_windows.ps1`, or `scripts/run_crypto_backtest.ps1`
- Classification: missing tests for important behavior
- Impact:
  - the current suite validates only the new PostgreSQL data-layer slice plus docs text presence
  - the repo's published CLI-first value proposition is still largely outside automated coverage

## Suite Health By Area

| Area | Layer | Health | Notes |
| --- | --- | --- | --- |
| PostgreSQL defaults | Unit | Pass | One isolated default-settings test runs without Docker |
| PostgreSQL schema / ingest / provenance / discovery / integrity / materialization | Integration | Blocked | 10 tests collect but fail at Docker-backed setup before assertions |
| Documentation contract | Contract | Pass | Presence-only check for README snippets and DB table names |
| CLI workflow / end-to-end coverage | E2E | Absent | No CLI smoke or end-to-end suite detected |
| Coverage measurement | Tooling | Unavailable | No runnable repo-owned coverage script |

## Validity Notes On Existing Tests

- `tests/test_docs_contract.py` is a valid lightweight contract test for documentation drift, but it should not be treated as runtime coverage for the referenced commands.
- The PostgreSQL integration tests appear structurally aligned with the current Phase 1 data layer and exercise meaningful behaviors once the database is available.
- Because the database suite could not get past environment setup in this audit run, assertion validity beyond collection-time inspection remains only partially verified.

## Missing-Test Areas

### Missing Unit Coverage

- `src/binance_market_data.py` for pagination, retry, malformed-response handling, and stalled cursor behavior
- `src/bootstrap_postgres.py` for argument parsing and `--skip-wait` behavior
- metric and helper-heavy legacy code in `src/evaluate_forecast.py`, `src/utils.py`, and `src/crypto_minute_backtest.py`

### Missing Integration Coverage

- `src/run_forecast.py` and `src/evaluate_forecast.py` for Yahoo/CSV ingestion and checkpoint-backed CLI behavior
- `src/crypto_minute_backtest.py` for SQLite schema maintenance, live mode, and backtest persistence
- PowerShell wrappers in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`

### Missing End-To-End Coverage

- no command-level smoke flow for the documented PostgreSQL Phase 1 workflow:
  - `bootstrap_postgres.py`
  - `postgres_ingest_binance.py`
  - `postgres_discover_data.py`
  - `postgres_verify_data.py`
  - `postgres_materialize_dataset.py`
- no end-to-end coverage for the legacy forecast, evaluation, and crypto backtest CLIs

## Blockers, Assumptions, And Unavailable Tooling

- This audit was run on 2026-04-13 from a Windows orchestration environment where Docker Desktop was not available.
- The repository's own docs position Linux, WSL, or Docker as the supported runtime for major flows, so the Docker dependency itself is not surprising; the lack of a smaller always-runnable subset is still a quality gap.
- The `.venv` environment is usable and contains `pytest 9.0.3`; the system Python does not.
- No committed test automation for discovery, coverage, or gap summarization was available under `scripts/testing/`.

## Prioritized Recommendations

1. Add a Docker-independent pytest subset or marker strategy so pure/default/contract tests always run even when PostgreSQL infrastructure is unavailable.
2. Restore or create the missing `scripts/testing/` audit helpers, or replace them with committed equivalents referenced by the helper workflow.
3. Add direct unit tests for `src/binance_market_data.py` and `src/bootstrap_postgres.py`.
4. Introduce CLI smoke tests for the documented PostgreSQL workflow and the main forecast/backtest entrypoints.
5. Decide whether coverage measurement should exist in-repo; if yes, add one committed command and record its expected environment.
