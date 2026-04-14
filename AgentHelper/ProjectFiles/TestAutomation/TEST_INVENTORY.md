# Test Inventory

- Date: 2026-04-13
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Collected tests: 12 via `.\.venv\Scripts\python.exe -m pytest --collect-only -q`

## Test Files

| Path | Layer | Current health | Main production surface touched |
| --- | --- | --- | --- |
| `tests/test_db_connection.py` | Unit + integration | 1 unit-style default-settings test passes; DB connectivity test is Docker-blocked | `src/postgres_dataset.py` |
| `tests/test_schema_bootstrap.py` | Integration | Docker-blocked | `src/postgres_dataset.py`, schema contract in `db/init/001_phase1_schema.sql` |
| `tests/test_binance_ingest.py` | Integration | Docker-blocked | `src/postgres_ingest_binance.py`, `src/postgres_dataset.py` |
| `tests/test_provenance.py` | Integration | Docker-blocked | `src/postgres_ingest_binance.py`, provenance writes in `src/postgres_dataset.py` |
| `tests/test_discovery_cli.py` | Integration | Docker-blocked | `src/postgres_discover_data.py`, `src/postgres_verify_data.py` |
| `tests/test_materialize_dataset.py` | Integration | Docker-blocked | `src/postgres_materialize_dataset.py`, CSV compatibility with `src/run_forecast.py` |
| `tests/test_docs_contract.py` | Contract | Passes | `README.md`, `db/README.md` |

## Layer Summary

| Layer | Present | Evidence | Health |
| --- | --- | --- | --- |
| Unit | Minimal | One pure default-settings test in `tests/test_db_connection.py`; the docs-snippet contract is also isolated | Runnable but thin |
| Integration | Yes | 10 PostgreSQL-backed tests across schema, ingest, discovery, integrity, provenance, and materialization | Non-runnable in this environment because all depend on Docker-backed PostgreSQL |
| E2E / workflow | No dedicated suite | No CLI smoke harness or browser runner detected | Gap for a CLI-first project |

## Collected Test Cases

1. `tests/test_binance_ingest.py::test_default_ingest_command_targets_btcusdt_last_year`
2. `tests/test_binance_ingest.py::test_rerunning_ingest_keeps_one_observation_per_timestamp`
3. `tests/test_db_connection.py::test_load_postgres_settings_uses_repo_defaults`
4. `tests/test_db_connection.py::test_project_code_connects_to_compose_managed_postgres`
5. `tests/test_discovery_cli.py::test_discovery_filters_and_sorting`
6. `tests/test_discovery_cli.py::test_integrity_report_surfaces_gap_and_minute_alignment_issues`
7. `tests/test_docs_contract.py::test_readme_and_db_readme_document_phase1_postgres_workflow`
8. `tests/test_materialize_dataset.py::test_series_csv_export_matches_forecast_csv_contract`
9. `tests/test_materialize_dataset.py::test_training_matrix_export_matches_train_preprocess_shape`
10. `tests/test_provenance.py::test_ingestion_run_records_source_range_and_completion_metadata`
11. `tests/test_schema_bootstrap.py::test_bootstrap_schema_creates_required_phase1_tables`
12. `tests/test_schema_bootstrap.py::test_observations_store_double_precision_with_a_future_upsert_key`

## Coverage Map By Production Area

### Covered Directly Or Indirectly

| Production area | Coverage shape | Notes |
| --- | --- | --- |
| `src/postgres_dataset.py` | Unit + integration | Defaults, connection path, schema bootstrap, provenance, and observation writes are exercised mostly through DB integration tests |
| `src/postgres_ingest_binance.py` | Integration | Default date-range and idempotent write behavior covered, but only behind PostgreSQL fixture setup |
| `src/postgres_discover_data.py` | Integration | Discovery filters and sorting covered |
| `src/postgres_verify_data.py` | Integration | Integrity-report issue counts covered |
| `src/postgres_materialize_dataset.py` | Integration | CSV export shape and compatibility with forecast CSV expectations covered |
| `README.md`, `db/README.md` | Contract | Presence-only documentation checks |

### Not Directly Covered

| Production area | Current test state |
| --- | --- |
| `src/bootstrap_postgres.py` | No direct test coverage |
| `src/binance_market_data.py` | No direct test coverage |
| `src/run_forecast.py` | No direct test coverage |
| `src/evaluate_forecast.py` | No direct test coverage |
| `src/crypto_minute_backtest.py` | No direct test coverage |
| `src/main.py` | No direct test coverage |
| `src/train.py` | No direct test coverage |
| `src/evaluation.py` | No direct test coverage |
| `src/train_flax.py` | No direct test coverage |
| `src/mock_trading.py` | No direct test coverage |
| `src/mock_trading_utils.py` | No direct test coverage |
| `configs/fine_tuning.py` | No direct test coverage |
| `scripts/setup_windows.ps1` | No direct test coverage |
| `scripts/run_crypto_backtest.ps1` | No direct test coverage |
| `scripts/precommit-checks.mjs` | Exercised manually during audit only; no automated test coverage detected |
