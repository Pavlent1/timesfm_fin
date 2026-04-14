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
| `node scripts/testing/discover-test-landscape.mjs --markdown` | Passed | Reported 17 collected pytest tests plus the new registered markers |
| `node scripts/testing/measure-coverage.mjs --markdown` | Passed | Coverage is explicitly unavailable because `pytest-cov` is not installed |
| `node scripts/testing/summarize-test-gaps.mjs --markdown` | Passed | Highlighted Docker-heavy integration concentration and direct-coverage gaps |
| `node scripts/precommit-checks.mjs` | Passed | Docker was reachable and the full pytest suite passed |
| `.\.venv\Scripts\python.exe -m pytest --collect-only -q` | Passed | Collected 17 tests |
| `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` | Passed | `7 passed, 10 deselected in 5.61s` |

## Collection Snapshot

- Total collected tests: 17
- Always-runnable non-Docker subset: 7
- Docker-marked integration tests: 10
- Dominant structure: one Docker-backed PostgreSQL fixture still underpins most integration tests, but the repo now has a stable non-Docker subset and tooling commands for audit workflows

## Coverage

- Coverage status: unavailable
- Reason:
  - `scripts/testing/measure-coverage.mjs` now runs successfully but reports that `pytest-cov` is not installed in the repo-managed Python environment
  - no other repo-owned coverage command or committed coverage configuration was detected during this audit refresh

## Blockers And Unavailable Areas

- Ten current tests still require Docker-managed PostgreSQL and are selected through the new `docker` marker.
- Coverage measurement is still unavailable until the repository decides to add a supported coverage plugin or alternative command.
- No dedicated browser or end-to-end runner is configured, which is consistent with the current CLI-only repository shape but still leaves workflow-smoke coverage absent.
