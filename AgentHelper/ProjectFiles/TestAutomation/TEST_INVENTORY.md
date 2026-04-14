# Test Inventory

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Collected tests: 48 via `.\.venv\Scripts\python.exe -m pytest --collect-only -q`

## Test Files

| Path | Layer | Current health | Main production surface touched |
| --- | --- | --- | --- |
| `tests/test_binance_ingest.py` | Integration (`docker`) | Passes in the current Docker-ready environment | `src/postgres_ingest_binance.py`, `src/postgres_dataset.py` |
| `tests/test_binance_market_data.py` | Unit | Passes in the non-Docker subset | `src/binance_market_data.py` |
| `tests/test_bootstrap_postgres.py` | Unit | Passes in the non-Docker subset | `src/bootstrap_postgres.py` |
| `tests/test_crypto_minute_backtest.py` | Unit | Passes in the non-Docker subset | `src/crypto_minute_backtest.py` |
| `tests/test_db_connection.py` | Unit + integration (`docker`) | Passes; one defaults test plus one Docker-backed connectivity test | `src/postgres_dataset.py` |
| `tests/test_discovery_cli.py` | Integration (`docker`) | Passes in the current Docker-ready environment | `src/postgres_discover_data.py`, `src/postgres_verify_data.py` |
| `tests/test_docs_contract.py` | Contract | Passes in the non-Docker subset | `README.md`, `db/README.md` |
| `tests/test_evaluate_forecast.py` | Unit | Passes in the non-Docker subset | `src/evaluate_forecast.py` |
| `tests/test_materialize_dataset.py` | Integration (`docker`) | Passes in the current Docker-ready environment | `src/postgres_materialize_dataset.py`, CSV compatibility with `src/run_forecast.py` |
| `tests/test_postgres_cli_contracts.py` | Unit / CLI contract | Passes in the non-Docker subset | `src/postgres_ingest_binance.py`, `src/postgres_discover_data.py`, `src/postgres_verify_data.py`, `src/postgres_materialize_dataset.py` |
| `tests/test_postgres_fixture_diagnostics.py` | Unit | Passes in the non-Docker subset | Docker failure reporting in `tests/conftest.py` |
| `tests/test_provenance.py` | Integration (`docker`) | Passes in the current Docker-ready environment | `src/postgres_ingest_binance.py`, provenance writes in `src/postgres_dataset.py` |
| `tests/test_run_forecast.py` | Unit | Passes in the non-Docker subset | `src/run_forecast.py` |
| `tests/test_schema_bootstrap.py` | Integration (`docker`) | Passes in the current Docker-ready environment | `src/postgres_dataset.py`, schema contract in `db/init/001_phase1_schema.sql` |
| `tests/test_script_wrappers.py` | Unit / wrapper contract | Passes in the non-Docker subset | `scripts/run_crypto_backtest.ps1`, `scripts/setup_windows.ps1` |
| `tests/test_testing_scripts.py` | Unit | Passes in the non-Docker subset | `scripts/testing/*.mjs` |

## Layer Summary

| Layer | Present | Evidence | Health |
| --- | --- | --- | --- |
| Unit | Yes | Direct coverage for market-data helpers, bootstrap CLI, forecast/evaluation/backtest helpers, testing scripts, wrapper contracts, and fixture diagnostics | Runnable without Docker |
| Contract | Yes | Documentation contract in `tests/test_docs_contract.py`; direct CLI-boundary checks in `tests/test_postgres_cli_contracts.py` and wrapper contract checks in `tests/test_script_wrappers.py` | Runnable without Docker |
| Integration | Yes | 10 PostgreSQL-backed tests across schema, ingest, discovery, integrity, provenance, and materialization | Passes when Docker is available; isolated behind the `docker` marker |
| E2E / workflow | No dedicated suite | No browser runner or end-to-end CLI harness detected | Still intentionally absent for this repo state |

## Coverage Map By Production Area

### Covered Directly Or Indirectly

| Production area | Coverage shape | Notes |
| --- | --- | --- |
| `src/binance_market_data.py` | Unit | Direct retry, malformed-response, de-duplication, and stalled-pagination assertions live in `tests/test_binance_market_data.py` |
| `src/bootstrap_postgres.py` | Unit / contract | Argument parsing, `--skip-wait`, schema-path plumbing, and collaborator calls are covered in `tests/test_bootstrap_postgres.py` |
| `src/postgres_dataset.py` | Unit + integration | Defaults, connection path, schema bootstrap, provenance, and observation writes are exercised through both isolated and Docker-backed tests |
| `src/postgres_ingest_binance.py` | Integration + CLI contract | Default date-range, idempotent writes, and command-summary behavior are covered |
| `src/postgres_discover_data.py` | Integration + CLI contract | Discovery filters, sorting, and CLI wiring are covered |
| `src/postgres_verify_data.py` | Integration + CLI contract | Integrity-report issue counts and CLI wiring are covered |
| `src/postgres_materialize_dataset.py` | Integration + CLI contract | CSV export shape, compatibility with forecast CSV expectations, and CLI mode routing are covered |
| `src/run_forecast.py` | Unit | CSV/Yahoo loading, future-index inference, model construction, and CLI output are covered without real checkpoint downloads |
| `src/evaluate_forecast.py` | Unit | Metric helpers, rolling-window aggregation, and formatted result output are covered |
| `src/crypto_minute_backtest.py` | Unit | SQLite schema, candle storage/loading, live preparation, live forecast output, backtest metrics, and persistence are covered |
| `scripts/run_crypto_backtest.ps1` | Wrapper contract | Docker command construction is covered with a fake `docker` executable |
| `scripts/setup_windows.ps1` | Wrapper contract | Python-version failure handling is covered with a fake `python` executable |
| `scripts/testing/_shared.mjs` | Unit | Exercised indirectly through the helper entrypoints in `tests/test_testing_scripts.py` |
| `scripts/testing/discover-test-landscape.mjs` | Unit | Direct subprocess coverage via `tests/test_testing_scripts.py` |
| `scripts/testing/measure-coverage.mjs` | Unit | Direct subprocess coverage via `tests/test_testing_scripts.py` |
| `scripts/testing/summarize-test-gaps.mjs` | Unit | Direct subprocess coverage via `tests/test_testing_scripts.py` |
| `scripts/testing/find-affected-tests.mjs` | Unit | Direct subprocess coverage via `tests/test_testing_scripts.py` |
| `scripts/testing/classify-test-level.mjs` | Unit | Direct subprocess coverage via `tests/test_testing_scripts.py` |
| `README.md`, `db/README.md` | Contract | Presence-only documentation checks |

### Not Directly Covered

| Production area | Current test state |
| --- | --- |
| `src/main.py` | No direct test coverage |
| `src/train.py` | No direct test coverage |
| `src/evaluation.py` | No direct test coverage |
| `src/train_flax.py` | No direct test coverage |
| `src/mock_trading.py` | No direct test coverage |
| `src/mock_trading_utils.py` | No direct test coverage |
| `src/utils.py` | No direct test coverage |
| `configs/fine_tuning.py` | No direct test coverage |
| `scripts/precommit-checks.mjs` | Exercised manually during audit and commit hooks only; no dedicated automated test coverage detected |
