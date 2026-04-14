# Test Audit

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Audit mode: repo inspection plus real command execution
- Preferences status: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` is `actionable` with conservative defaults still in effect for unresolved CI and threshold decisions

## Commands Run

- `node scripts/testing/discover-test-landscape.mjs --markdown`
- `node scripts/testing/measure-coverage.mjs --markdown`
- `node scripts/testing/summarize-test-gaps.mjs --markdown`
- `node scripts/precommit-checks.mjs`
- `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
- `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`

## Severity-Ordered Findings

### 1. Missing Coverage Measurement: the repo now has a coverage command, but coverage is still unavailable

- Evidence:
  - `node scripts/testing/measure-coverage.mjs --markdown` passed
  - the script reported coverage status `unavailable`
  - the current reason is that `pytest-cov` is not installed in the repo-managed Python environment
- Classification: missing coverage measurement
- Impact:
  - Wave 1 fixed the missing-command failure mode, but the repository still cannot quantify coverage deltas
  - later audit and planning work still need to treat coverage as advisory-unavailable instead of measured

### 2. Fragile Layer Balance Remains: most integration signal still sits behind the same Docker-backed fixture

- Evidence:
  - `.\.venv\Scripts\python.exe -m pytest --collect-only -q` collected 17 tests
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` passed with `7 passed, 10 deselected`
  - the remaining 10 tests are still concentrated in the PostgreSQL fixture stack rooted in `tests/conftest.py`
- Classification: fragile pattern and incorrect layer balance
- Impact:
  - the new non-Docker subset restores fast reusable feedback, which resolves the original Wave 1 blocker
  - however, most application-behavior coverage still depends on Docker-backed PostgreSQL setup and can fail as a group when that environment is unavailable

### 3. Important Shared Adapters And CLIs Still Have No Direct Tests

- Evidence:
  - `node scripts/testing/summarize-test-gaps.mjs --markdown` lists `src/binance_market_data.py` and `src/bootstrap_postgres.py` among the direct-coverage gaps
  - the current inventory still finds no dedicated tests for those files
- Classification: missing tests for important behavior
- Impact:
  - failures in shared market-data fetch logic or the bootstrap CLI can still surface late through larger workflows
  - these remain the next high-value targets after the Wave 1 groundwork

### 4. Core Forecasting, Backtesting, And Legacy Training Surfaces Remain Untested

- Evidence:
  - the refreshed inventory still shows no direct tests for `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/mock_trading.py`, `src/mock_trading_utils.py`, `configs/fine_tuning.py`, `scripts/setup_windows.ps1`, or `scripts/run_crypto_backtest.ps1`
- Classification: missing tests for important behavior
- Impact:
  - the repository's published forecasting and backtesting workflows still sit outside automated coverage
  - the current suite remains strongest around the PostgreSQL data pipeline plus the new Wave 1 tooling scripts

## Wave 1 Resolution Notes

- The previously missing `scripts/testing/` helper commands now exist and run from the repo root.
- The repository now registers `unit`, `contract`, `integration`, and `docker` markers through `pytest.ini`.
- The always-runnable subset is now explicit and verified with `pytest -m "not docker"`.
- In the current Docker-ready environment, `node scripts/precommit-checks.mjs` and the full pytest suite both pass.

## Suite Health By Area

| Area | Layer | Health | Notes |
| --- | --- | --- | --- |
| Test discovery and gap-reporting helper scripts | Tooling | Pass | `scripts/testing/` commands now exist and run successfully |
| Always-runnable non-Docker subset | Unit + contract | Pass | `7 passed, 10 deselected` |
| PostgreSQL schema / ingest / provenance / discovery / integrity / materialization | Integration (`docker`) | Pass in current environment | Still concentrated behind one Docker-backed fixture |
| Documentation contract | Contract | Pass | Lightweight drift check only; not runtime coverage |
| Coverage measurement | Tooling | Unavailable | Command now exists, but the plugin is not installed |
| CLI workflow / end-to-end coverage | E2E | Absent | No CLI smoke or end-to-end suite detected |

## Validity Notes On Existing Tests

- `tests/test_docs_contract.py` remains a valid lightweight contract test for documentation drift, but it should not be treated as runtime coverage for the referenced commands.
- The PostgreSQL integration tests still appear structurally aligned with the current Phase 1 data layer and now pass in a Docker-ready environment.
- `tests/test_testing_scripts.py` gives the Wave 1 helper commands direct regression protection without introducing a second test runner.

## Missing-Test Areas

### Missing Unit Coverage

- `src/binance_market_data.py` for pagination, retry, malformed-response handling, and stalled cursor behavior
- `src/bootstrap_postgres.py` for argument parsing, readiness waiting, and `--skip-wait` behavior
- helper and metric-heavy logic in `src/evaluate_forecast.py`, `src/utils.py`, and `src/crypto_minute_backtest.py`

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

- This audit was run on 2026-04-14 from the repository root in a Windows environment where Docker was reachable.
- The repository's own docs still position Linux, WSL, or Docker as the supported runtime for major flows, so Docker-backed integration is expected for part of the suite.
- The `.venv` environment remains the working Python test environment; the system Python is still not the primary validated path for these workflows.
- Coverage measurement remains intentionally unavailable until the project chooses a supported in-repo coverage mechanism.

## Prioritized Recommendations

1. Execute Wave 2 next to add direct tests for `src/binance_market_data.py` and `src/bootstrap_postgres.py`.
2. Decide whether the project wants a committed coverage plugin or another supported measurement command, then update `scripts/testing/measure-coverage.mjs` accordingly.
3. Continue reducing Docker concentration by adding more deterministic unit and contract tests around shared helpers and CLI boundaries.
4. Add CLI smoke or contract coverage for the documented forecast and backtest entrypoints once the Wave 2 adapter work is complete.
