# Test Audit

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Audit mode: repo inspection plus real command execution
- Preferences status: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` is `actionable` with conservative defaults still in effect for unresolved CI and threshold decisions

## Commands Run

- `node scripts/testing/discover-test-landscape.mjs --markdown`
- `node scripts/testing/measure-coverage.mjs --markdown`
- `node scripts/testing/summarize-test-gaps.mjs --markdown`
- `.\.venv\Scripts\python.exe -m pytest tests/test_postgres_cli_contracts.py tests/test_postgres_fixture_diagnostics.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_db_connection.py tests/test_schema_bootstrap.py tests/test_binance_ingest.py tests/test_discovery_cli.py tests/test_materialize_dataset.py tests/test_provenance.py -q -m "docker"`
- `.\.venv\Scripts\python.exe -m pytest tests/test_run_forecast.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_evaluate_forecast.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_crypto_minute_backtest.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_script_wrappers.py -q`
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
  - Waves 3 and 4 materially improved direct coverage, but the repository still cannot measure coverage percentages or deltas
  - later audit and planning work must continue treating coverage as advisory-unavailable instead of measured

### 2. Remaining Direct-Coverage Gaps Are Now Concentrated In Legacy Training And Shared Utility Surfaces

- Evidence:
  - `node scripts/testing/summarize-test-gaps.mjs --markdown` now reports only:
    - `src/evaluation.py`
    - `src/mock_trading.py`
    - `src/mock_trading_utils.py`
    - `src/train_flax.py`
    - `src/utils.py`
    - `configs/fine_tuning.py`
    - `scripts/precommit-checks.mjs`
- Classification: missing tests for important behavior
- Impact:
  - the forecast, evaluation, crypto backtest, and Windows wrapper gaps called out by the previous audit are now closed
  - the remaining uncovered area is mostly legacy training and utility code, which is still a real risk but a narrower one than before

### 3. Docker Still Gates The PostgreSQL Integration Layer, But It No Longer Masks Most Test Signal

- Evidence:
  - `.\.venv\Scripts\python.exe -m pytest --collect-only -q` collected 48 tests
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` passed with `38 passed, 10 deselected`
  - `.\.venv\Scripts\python.exe -m pytest ... -m "docker"` passed with `10 passed, 1 deselected`
  - `node scripts/precommit-checks.mjs` passed with the full 48-test suite
- Classification: fragile infrastructure dependency
- Impact:
  - Docker is still required for the Phase 1 PostgreSQL integration layer
  - however, a Docker outage now removes only the integration slice instead of most of the repository's usable test signal

### 4. No Dedicated End-To-End Runner Exists, But The Repository Now Has Stronger CLI Contract Coverage Instead

- Evidence:
  - no browser or E2E runner was discovered
  - Waves 3 and 4 added direct contract coverage for the PostgreSQL CLIs and the Windows wrapper scripts
- Classification: intentional E2E absence with mitigating contract coverage
- Impact:
  - there is still no end-to-end runner for a full CLI workflow chain
  - the repository now has deterministic command-boundary protection that matches the current CLI-only product shape better than a browser-first E2E stack would

## Wave Resolution Notes

### Wave 3

- `tests/conftest.py` now reports clearer infrastructure failures for missing or broken Docker commands and for PostgreSQL readiness timeouts.
- `tests/test_postgres_cli_contracts.py` adds direct command-summary and CLI-wiring coverage for:
  - `src/postgres_ingest_binance.py`
  - `src/postgres_discover_data.py`
  - `src/postgres_verify_data.py`
  - `src/postgres_materialize_dataset.py`
- `tests/test_postgres_fixture_diagnostics.py` adds non-Docker regression coverage for the fixture-diagnostics behavior itself.
- The Docker-backed PostgreSQL suite passes in the current environment and is now easier to diagnose when infrastructure breaks.

### Wave 4

- `tests/test_run_forecast.py` adds deterministic coverage for CSV/Yahoo loading, future-index inference, model construction, and main-path CLI output without real checkpoint downloads.
- `tests/test_evaluate_forecast.py` adds direct metric, rolling-window, and formatting coverage.
- `tests/test_crypto_minute_backtest.py` adds coverage for SQLite schema/storage, live preparation, live forecast output, backtest metrics, and persistence.
- `tests/test_script_wrappers.py` adds contract checks for the Windows wrapper scripts using fake `docker` and `python` executables.
- `scripts/setup_windows.ps1` was fixed so its failure message safely interpolates `${LASTEXITCODE}` instead of triggering a PowerShell parsing error.

## Suite Health By Area

| Area | Layer | Health | Notes |
| --- | --- | --- | --- |
| Shared Binance market-data adapter | Unit | Pass | Direct regression coverage exists for retry, malformed payloads, de-duplication, and pagination stall guards |
| PostgreSQL CLI and fixture diagnostics | Unit / contract | Pass | Direct CLI-boundary and fixture-failure coverage exists in the non-Docker subset |
| Always-runnable non-Docker subset | Unit + contract | Pass | `38 passed, 10 deselected` |
| PostgreSQL schema / ingest / provenance / discovery / integrity / materialization | Integration (`docker`) | Pass in current environment | Still requires Docker, but is isolated behind the `docker` marker |
| Forecast, evaluation, and crypto backtest helpers | Unit | Pass | Deterministic coverage added without TimesFM checkpoint downloads |
| Windows wrapper scripts | Contract-style unit | Pass | Docker and Python boundaries are stubbed through fake executables |
| Documentation contract | Contract | Pass | Lightweight drift check only; not runtime coverage |
| Coverage measurement | Tooling | Unavailable | Command exists, but the coverage plugin is not installed |

## Validity Notes On Existing Tests

- `tests/test_docs_contract.py` remains a valid lightweight contract test for documentation drift, but it should not be treated as runtime coverage for the referenced commands.
- The Wave 3 fixture-diagnostics changes make Docker failures clearer without weakening the Docker-backed integration gate.
- The Wave 4 tests avoid real TimesFM checkpoint downloads, live Yahoo/Binance network calls, and real Docker execution while still asserting observable behavior at the helper and wrapper boundaries.
- `tests/test_script_wrappers.py` found and verified a real bug fix in `scripts/setup_windows.ps1`.

## Missing-Test Areas

### Missing Unit Coverage

- legacy orchestration helpers in `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/mock_trading.py`, and `src/mock_trading_utils.py`
- shared numeric helpers in `src/utils.py`
- hyperparameter/config behavior in `configs/fine_tuning.py`

### Missing Integration Or Tooling Coverage

- `scripts/precommit-checks.mjs` still has no dedicated automated tests even though it is exercised by audit and hook execution

### Missing End-To-End Coverage

- no dedicated end-to-end harness for a full PostgreSQL CLI chain
- no dedicated end-to-end harness for the forecast or crypto backtest workflows

## Blockers, Assumptions, And Unavailable Tooling

- This audit was run on 2026-04-14 from the repository root in a Windows environment where Docker was reachable.
- The `.venv` environment remains the working Python test environment; the system Python is still not the primary validated path for these workflows.
- Coverage measurement remains intentionally unavailable until the project chooses a supported in-repo coverage mechanism.
- No browser/E2E runner is configured, which remains aligned with the current CLI-only repository shape and saved preferences.

## Prioritized Recommendations

1. Execute Wave 5 next to re-measure the test landscape formally, refresh the baseline artifacts again if anything changes, and record explicit deferrals for the remaining uncovered legacy areas.
2. Decide whether the project wants a committed coverage plugin or another supported measurement command, then update `scripts/testing/measure-coverage.mjs` accordingly.
3. If additional test investment continues after Wave 5, focus on `src/evaluation.py`, `src/utils.py`, and the legacy training-orchestration surfaces before widening into new frameworks.
