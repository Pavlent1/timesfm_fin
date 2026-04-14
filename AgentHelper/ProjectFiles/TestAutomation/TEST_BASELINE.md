# Test Baseline

- Date: 2026-04-14
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`) plus the current `tests/` tree
- Preferences file: `TEST_PREFERENCES.yaml` remains `actionable` with conservative defaults still open for CI thresholds and later policy refinements
- Refresh note: Wave 5 validation re-ran the repo-owned discovery, gap, pytest-slice, and precommit commands from the repository root

## Runners Detected

| Runner | Version / status | Notes |
| --- | --- | --- |
| `pytest` | `9.0.3` from `.\.venv\Scripts\python.exe` | The repo-local virtual environment remains the verified runnable pytest environment |
| Node.js helper scripts | Present under `scripts/testing/` | Discovery, coverage-status, gap-summary, affected-test, and classification commands all run successfully |
| Browser / E2E runner | Not detected | No Playwright, Cypress, Jest, Vitest, or browser app surface detected |

## Commands Run

| Command | Result | Notes |
| --- | --- | --- |
| `node scripts/testing/discover-test-landscape.mjs --markdown` | Passed | Reported 48 collected pytest tests and the current marker split |
| `node scripts/testing/measure-coverage.mjs --markdown` | Passed | Coverage is explicitly unavailable because `pytest-cov` is not installed |
| `node scripts/testing/summarize-test-gaps.mjs --markdown` | Passed | Remaining direct-coverage gaps are now limited to legacy helpers, `configs/fine_tuning.py`, and `scripts/precommit-checks.mjs` |
| `.\.venv\Scripts\python.exe -m pytest tests/test_testing_scripts.py -q` | Passed | `5 passed in 3.08s` for the tooling-level regression slice that covers discovery, coverage-status, gap-summary, affected-test, and classification commands |
| `.\.venv\Scripts\python.exe -m pytest --collect-only -q` | Passed | Collected 48 tests |
| `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` | Passed | `38 passed, 10 deselected in 5.48s` |
| `.\.venv\Scripts\python.exe -m pytest -q -m "docker"` | Passed | `10 passed, 38 deselected in 3.44s` for the isolated PostgreSQL integration layer |
| `node scripts/precommit-checks.mjs` | Passed | Docker was reachable and the full pytest suite passed with 48 tests |

## Collection Snapshot

- Total collected tests: 48
- Always-runnable non-Docker subset: 38
- Docker-marked integration tests: 10
- Dominant structure:
  - the fast subset now covers tooling, shared adapters, PostgreSQL CLI contracts, forecast/evaluation/backtest helpers, and the Windows wrappers
  - Docker remains required only for the PostgreSQL integration layer rooted in `tests/conftest.py`

## Coverage

- Coverage status: unavailable
- Reason:
  - `scripts/testing/measure-coverage.mjs` runs successfully but reports that `pytest-cov` is not installed in the repo-managed Python environment
  - no other repo-owned coverage command or committed coverage configuration was detected during this audit refresh

## Blockers And Unavailable Areas

- Coverage measurement is still unavailable until the repository decides to add a supported coverage plugin or alternative command.
- Ten current tests still require Docker-managed PostgreSQL and are selected through the `docker` marker, but the suite is now clearly isolated from the 38-test non-Docker subset.
- No dedicated browser or end-to-end runner is configured, which still matches the current CLI-only repository shape.
- CI-stage enforcement outside the existing pre-commit hook and any hard coverage threshold remain intentionally undecided until preferences are confirmed.
