# Test Audit

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Audit mode: repo inspection plus real command execution
- Preferences status: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` is `actionable` with conservative defaults still in effect for unresolved CI and threshold decisions

## Commands Run

- `node scripts/testing/discover-test-landscape.mjs --markdown`
- `node scripts/testing/measure-coverage.mjs --markdown`
- `node scripts/testing/summarize-test-gaps.mjs --markdown`
- `.\.venv\Scripts\python.exe -m pytest tests/test_binance_market_data.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_bootstrap_postgres.py -q`
- `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
- `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
- `node scripts/precommit-checks.mjs`

## Severity-Ordered Findings

### 1. Missing Coverage Measurement: the repo still cannot quantify coverage deltas

- Evidence:
  - `node scripts/testing/measure-coverage.mjs --markdown` passed
  - the script reported coverage status `unavailable`
  - the current reason is that `pytest-cov` is not installed in the repo-managed Python environment
- Classification: missing coverage measurement
- Impact:
  - the repository now has more direct tests, but it still cannot measure how much risk each wave removes
  - later audit and planning work must continue treating coverage as advisory-unavailable instead of measured

### 2. Docker Concentration Remains: a large portion of application-behavior coverage still depends on the shared PostgreSQL fixture stack

- Evidence:
  - `.\.venv\Scripts\python.exe -m pytest --collect-only -q` collected 25 tests
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` passed with `15 passed, 10 deselected`
  - `node scripts/precommit-checks.mjs` passed with the full 25-test suite, but six of the ten collected test files still rely on Docker-backed PostgreSQL fixtures rooted in `tests/conftest.py`
- Classification: fragile pattern and incorrect layer balance
- Impact:
  - Wave 2 materially improved the always-runnable subset
  - however, a Docker outage would still remove a large share of the repository's application-behavior signal at once

### 3. Core Forecasting, Backtesting, And Legacy Training Surfaces Still Lack Direct Tests

- Evidence:
  - the refreshed inventory still shows no direct tests for `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/mock_trading.py`, `src/mock_trading_utils.py`, `src/utils.py`, `configs/fine_tuning.py`, `scripts/setup_windows.ps1`, or `scripts/run_crypto_backtest.ps1`
  - `node scripts/testing/summarize-test-gaps.mjs --markdown` still lists the forecast/backtest helpers, wrapper scripts, and legacy utilities among the missing direct-coverage areas
- Classification: missing tests for important behavior
- Impact:
  - the repository's published forecasting and crypto-backtest workflows still sit mostly outside direct automated coverage
  - the training stack remains intentionally light-tested and should stay an explicit deferral rather than an assumed safe area

### 4. End-To-End CLI Workflow Coverage Is Still Absent

- Evidence:
  - no dedicated CLI smoke harness or end-to-end runner was discovered
  - Wave 2 added direct unit and contract coverage for `src/bootstrap_postgres.py`, but there is still no workflow-level smoke path that exercises the documented PostgreSQL CLI chain end to end
- Classification: missing tests for important behavior
- Impact:
  - command-boundary regressions are less risky than before, but cross-command workflow failures can still surface late
  - future waves should keep using contract and deterministic smoke coverage instead of introducing a browser-first E2E stack that the preferences do not support

## Wave 2 Resolution Notes

- `tests/test_binance_market_data.py` now covers HTTP 429 retry handling, malformed payload rejection, duplicate timestamp de-duplication, and stalled-cursor protection for `src/binance_market_data.py`.
- `tests/test_bootstrap_postgres.py` now covers argument defaults, `--skip-wait`, schema-file plumbing, and the main-command collaborator calls for `src/bootstrap_postgres.py`.
- `tests/test_testing_scripts.py` was updated so the gap summary no longer expects the Wave 2 targets to appear as uncovered.
- In the current Docker-ready environment, `node scripts/precommit-checks.mjs` and the full pytest suite both pass with 25 tests.

## Suite Health By Area

| Area | Layer | Health | Notes |
| --- | --- | --- | --- |
| Shared Binance market-data adapter | Unit | Pass | Direct regression coverage now exists for retry, malformed payloads, de-duplication, and pagination stall guards |
| PostgreSQL bootstrap CLI | Unit / contract | Pass | Direct regression coverage now exists for defaults, `--skip-wait`, schema path plumbing, and collaborator orchestration |
| Always-runnable non-Docker subset | Unit + contract | Pass | `15 passed, 10 deselected` |
| PostgreSQL schema / ingest / provenance / discovery / integrity / materialization | Integration (`docker`) | Pass in current environment | Still concentrated behind one Docker-backed fixture family |
| Documentation contract | Contract | Pass | Lightweight drift check only; not runtime coverage |
| Coverage measurement | Tooling | Unavailable | Command exists, but the plugin is not installed |
| CLI workflow / end-to-end coverage | E2E | Absent | No CLI smoke or browser runner detected |

## Validity Notes On Existing Tests

- `tests/test_docs_contract.py` remains a valid lightweight contract test for documentation drift, but it should not be treated as runtime coverage for the referenced commands.
- The new Wave 2 tests avoid real network and Docker dependencies while still asserting observable collaborator behavior for the shared adapter and bootstrap CLI.
- The PostgreSQL integration tests still appear structurally aligned with the current Phase 1 data layer and now pass in a Docker-ready environment.
- `tests/test_testing_scripts.py` continues to give the helper entrypoints direct regression protection without introducing a second test runner.

## Missing-Test Areas

### Missing Unit Coverage

- helper and metric-heavy logic in `src/evaluate_forecast.py`, `src/utils.py`, and `src/crypto_minute_backtest.py`
- legacy orchestration helpers in `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/mock_trading.py`, and `src/mock_trading_utils.py`

### Missing Integration Coverage

- `src/run_forecast.py` and `src/evaluate_forecast.py` for Yahoo/CSV ingestion and checkpoint-adjacent CLI behavior
- `src/crypto_minute_backtest.py` for SQLite schema maintenance, live mode, and backtest persistence
- PowerShell wrappers in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`

### Missing End-To-End Coverage

- no command-level smoke flow for the documented PostgreSQL Phase 1 workflow:
  - `bootstrap_postgres.py`
  - `postgres_ingest_binance.py`
  - `postgres_discover_data.py`
  - `postgres_verify_data.py`
  - `postgres_materialize_dataset.py`
- no end-to-end coverage for the forecast, evaluation, and crypto backtest CLIs

## Blockers, Assumptions, And Unavailable Tooling

- This audit was run on 2026-04-14 from the repository root in a Windows environment where Docker was reachable.
- The repository's own docs still position Linux, WSL, or Docker as the supported runtime for major flows, so Docker-backed integration is expected for part of the suite.
- The `.venv` environment remains the working Python test environment; the system Python is still not the primary validated path for these workflows.
- Coverage measurement remains intentionally unavailable until the project chooses a supported in-repo coverage mechanism.

## Prioritized Recommendations

1. Execute Wave 3 next to harden PostgreSQL workflow contracts, diagnostics, and the Docker-backed integration split.
2. Decide whether the project wants a committed coverage plugin or another supported measurement command, then update `scripts/testing/measure-coverage.mjs` accordingly.
3. Continue with Wave 4 after Wave 3 to add deterministic coverage for `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and the Windows wrapper scripts.
4. Keep reducing Docker concentration by favoring deterministic unit and contract tests when a full integration environment is not required.
