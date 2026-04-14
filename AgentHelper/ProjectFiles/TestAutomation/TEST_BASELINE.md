# Test Baseline

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`) plus the current `tests/` tree
- Preferences file: `TEST_PREFERENCES.yaml` is `actionable` with conservative defaults still open for CI thresholds and later policy refinements

## Runners Detected

| Runner | Version / status | Notes |
| --- | --- | --- |
| `pytest` | `9.0.3` from `.\.venv\Scripts\python.exe` | The repo-local virtual environment remains the verified runnable pytest environment |
| Node.js helper scripts | Present under `scripts/testing/` | Discovery, coverage-status, gap-summary, affected-test, and classification commands now exist |
| Browser / E2E runner | Not detected | No Playwright, Cypress, Jest, Vitest, or browser app surface detected |

## Commands Run

| Command | Result | Notes |
| --- | --- | --- |
| `node scripts/testing/discover-test-landscape.mjs --markdown` | Passed | Reported 25 collected pytest tests and the current marker split |
| `node scripts/testing/measure-coverage.mjs --markdown` | Passed | Coverage is explicitly unavailable because `pytest-cov` is not installed |
| `node scripts/testing/summarize-test-gaps.mjs --markdown` | Passed | No longer lists `src/binance_market_data.py` or `src/bootstrap_postgres.py` as direct-coverage gaps |
| `.\.venv\Scripts\python.exe -m pytest tests/test_binance_market_data.py -q` | Passed | `4 passed in 0.04s` for the Binance adapter unit coverage slice |
| `.\.venv\Scripts\python.exe -m pytest tests/test_bootstrap_postgres.py -q` | Passed | `4 passed in 0.03s` for the bootstrap CLI contract slice |
| `.\.venv\Scripts\python.exe -m pytest --collect-only -q` | Passed | Collected 25 tests |
| `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` | Passed | `15 passed, 10 deselected in 5.36s` |
| `node scripts/precommit-checks.mjs` | Passed | Docker was reachable and the full pytest suite passed with 25 tests |

## Collection Snapshot

- Total collected tests: 25
- Always-runnable non-Docker subset: 15
- Docker-marked integration tests: 10
- Dominant structure: the fast subset is materially stronger after Wave 2, but six of the ten collected test files still depend on the shared Docker-backed PostgreSQL fixture stack

## Coverage

- Coverage status: unavailable
- Reason:
  - `scripts/testing/measure-coverage.mjs` runs successfully but reports that `pytest-cov` is not installed in the repo-managed Python environment
  - no other repo-owned coverage command or committed coverage configuration was detected during this audit refresh

## Blockers And Unavailable Areas

- Ten current tests still require Docker-managed PostgreSQL and are selected through the `docker` marker.
- Coverage measurement is still unavailable until the repository decides to add a supported coverage plugin or alternative command.
- No dedicated browser or end-to-end runner is configured, which matches the current CLI-only repository shape but still leaves workflow-smoke coverage absent.
