---
artifact: global-autotest-execution
status: in_progress
updated: 2026-04-14
plan: AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md
---

# Global Automated Test Execution

## Wave Summary

- Overall status: `in_progress`
- Current wave: `Wave 5`
- Next wave: `None`
- Current step: Waves 3 and 4 are complete and the audit artifacts now reflect the broader direct-coverage footprint
- Next step: execute Wave 5 coverage refresh and deferral recording
- Next recommended command: `Use $helper-test-execute-plan wave 5`

## Preflight

- Date: `2026-04-14`
- Result: `resolved`
- Original blocker: the execution log was missing when this workflow was first resumed on 2026-04-14
- Resolution applied: the execution log was created, then maintained wave by wave so later runs can resume safely

## Waves

| Wave | Status | Completed scopes | Commands run | Failures encountered | Blockers | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `complete` | Scope A `scripts/testing/` helper restoration; Scope B pytest marker/config split; Scope C audit refresh | `helper-test-execute-plan` preflight; `node .codex/get-shit-done/bin/gsd-tools.cjs init quick "execute wave 1 of the global autotest plan"`; helper-script validation; `.\.venv\Scripts\python.exe -m pytest --collect-only -q`; `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`; `node scripts/precommit-checks.mjs` | Resolved during scope work: gap summarizer initially counted docs-contract mentions as direct coverage; affected-test parsing initially mangled porcelain paths | None active | Coverage measurement unavailable; later waves still pending |
| 2 | `complete` | Scope A `src/binance_market_data.py`; Scope B `src/bootstrap_postgres.py` | `node .codex/get-shit-done/bin/gsd-tools.cjs init quick "execute wave 2 of the global autotest plan"`; classifier runs for Wave 2 sources; `.\.venv\Scripts\python.exe -m pytest tests/test_binance_market_data.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_bootstrap_postgres.py -q`; `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`; helper-script refresh; `node scripts/precommit-checks.mjs` | Resolved during scope work: Windows path separator assertion mismatch in `tests/test_bootstrap_postgres.py`; stale gap-summary expectation in `tests/test_testing_scripts.py` | None active | PostgreSQL workflow contracts and forecast/backtest coverage still pending |
| 3 | `complete` | Scope A fixture diagnostics and marker hygiene in `tests/conftest.py`; Scope B CLI contracts for ingest/provenance paths; Scope C CLI contracts for discovery/verify/materialize paths | `node .codex/get-shit-done/bin/gsd-tools.cjs init quick "execute waves 3 and 4 of the global autotest plan"`; classifier runs for `tests/conftest.py` and PostgreSQL CLI files; `docker info`; `.\.venv\Scripts\python.exe -m pytest tests/test_postgres_cli_contracts.py tests/test_postgres_fixture_diagnostics.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_db_connection.py tests/test_schema_bootstrap.py tests/test_binance_ingest.py tests/test_discovery_cli.py tests/test_materialize_dataset.py tests/test_provenance.py -q -m "docker"`; `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`; `node scripts/precommit-checks.mjs` | Resolved during scope work: new discovery contract test initially omitted timestamp columns; fixture-diagnostics test initially used the wrong `CalledProcessError` payload field | None active | Docker is still required for the PostgreSQL integration slice, but failures are now more diagnosable and isolated |
| 4 | `complete` | Scope A `src/run_forecast.py`; Scope B `src/evaluate_forecast.py`; Scope C `src/crypto_minute_backtest.py`; Scope D Windows wrapper contracts | classifier runs for Wave 4 sources and scripts; `.\.venv\Scripts\python.exe -m pytest tests/test_run_forecast.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_evaluate_forecast.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_crypto_minute_backtest.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_script_wrappers.py -q`; `.\.venv\Scripts\python.exe -m pytest tests/test_testing_scripts.py -q`; `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`; `node scripts/precommit-checks.mjs`; audit refresh commands | Resolved during scope work: `tests/test_script_wrappers.py` exposed a real PowerShell interpolation bug in `scripts/setup_windows.ps1`; `tests/test_testing_scripts.py` still expected `src/crypto_minute_backtest.py` to appear as uncovered; `src/evaluate_forecast.py` emitted a pandas deprecation warning and was updated to avoid it | None active | Remaining direct-coverage gaps are now limited to legacy training/utilities, `configs/fine_tuning.py`, and `scripts/precommit-checks.mjs` |
| 5 | `pending` | None | None | None | Depends on Waves 1-4 | Coverage measurement remains unavailable and explicit deferrals still need final recording |

## Wave 4 Detail

- Status: `complete`
- Completed scopes:
  - Scope A: added `tests/test_run_forecast.py` for CSV/Yahoo loading, future-index inference, model construction, and CLI output
  - Scope B: added `tests/test_evaluate_forecast.py` for metric helpers, rolling-window aggregation, and result formatting
  - Scope C: added `tests/test_crypto_minute_backtest.py` for SQLite persistence, live preparation, live forecast output, backtest metrics, and saved runs
  - Scope D: added `tests/test_script_wrappers.py` for wrapper command contracts and fixed `scripts/setup_windows.ps1`
- Commands run:
  - `node scripts/testing/classify-test-level.mjs --source src/run_forecast.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/evaluate_forecast.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/crypto_minute_backtest.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source scripts/run_crypto_backtest.ps1 --markdown`
  - `node scripts/testing/classify-test-level.mjs --source scripts/setup_windows.ps1 --markdown`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_forecast.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_evaluate_forecast.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_crypto_minute_backtest.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_script_wrappers.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_testing_scripts.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
  - `node scripts/precommit-checks.mjs`
  - `node scripts/testing/discover-test-landscape.mjs --markdown`
  - `node scripts/testing/measure-coverage.mjs --markdown`
  - `node scripts/testing/summarize-test-gaps.mjs --markdown`
- Failures encountered:
  - `tests/test_script_wrappers.py` found that `scripts/setup_windows.ps1` used `$LASTEXITCODE:` instead of `${LASTEXITCODE}` inside a throw string
  - `tests/test_testing_scripts.py` still expected the old Wave 4 gaps to remain uncovered
  - `src/evaluate_forecast.py` emitted a pandas deprecation warning from `DataFrame.applymap`
- Blockers:
  - None active
- Remaining risk:
  - Wave 4 is complete, but coverage is still unmeasured and legacy training-oriented surfaces remain lightly tested

## Wave 3 Detail

- Status: `complete`
- Completed scopes:
  - Scope A: improved Docker fixture diagnostics and marker hygiene in `tests/conftest.py`
  - Scope B: added PostgreSQL ingest and summary contract coverage
  - Scope C: added discovery, verify, and materialize CLI contract coverage
- Commands run:
  - `docker info`
  - `node scripts/testing/classify-test-level.mjs --source tests/conftest.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/bootstrap_postgres.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/postgres_ingest_binance.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/postgres_discover_data.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/postgres_verify_data.py --markdown`
  - `node scripts/testing/classify-test-level.mjs --source src/postgres_materialize_dataset.py --markdown`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_postgres_cli_contracts.py tests/test_postgres_fixture_diagnostics.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_db_connection.py tests/test_schema_bootstrap.py tests/test_binance_ingest.py tests/test_discovery_cli.py tests/test_materialize_dataset.py tests/test_provenance.py -q -m "docker"`
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
  - `node scripts/precommit-checks.mjs`
- Failures encountered:
  - the first CLI contract draft for discovery did not match the real rendered table format
  - the first fixture-diagnostics test used `stdout=` instead of `output=` for `CalledProcessError`
- Blockers:
  - None active
- Remaining risk:
  - Docker is still required for the PostgreSQL integration slice, but the suite is now smaller, better isolated, and easier to diagnose
