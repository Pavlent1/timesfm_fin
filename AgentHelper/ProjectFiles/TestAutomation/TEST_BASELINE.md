# Test Baseline

- Date: 2026-04-13
- Scope: whole approved codebase (`src/`, `configs/`, `scripts/`) plus the current `tests/` tree
- Preferences file: `TEST_PREFERENCES.yaml` exists but is still `draft`, so it was treated as advisory only

## Runners Detected

| Runner | Version / status | Notes |
| --- | --- | --- |
| `pytest` | `9.0.3` from `.\.venv\Scripts\python.exe` | The repo-local virtual environment is the only verified runnable pytest environment |
| Node.js helper scripts | Present | `scripts/precommit-checks.mjs` exists and is the repo-managed pre-commit test gate |
| Browser / E2E runner | Not detected | No Playwright, Cypress, Jest, Vitest, or browser app surface detected |

## Commands Run

| Command | Result | Notes |
| --- | --- | --- |
| `node scripts/testing/discover-test-landscape.mjs --markdown` | Failed | `MODULE_NOT_FOUND`; script is absent |
| `node scripts/testing/measure-coverage.mjs --markdown` | Failed | `MODULE_NOT_FOUND`; script is absent |
| `node scripts/testing/summarize-test-gaps.mjs --markdown` | Failed | `MODULE_NOT_FOUND`; script is absent |
| `node scripts/precommit-checks.mjs` | Failed | Docker check failed before pytest started |
| `python -m pytest --collect-only -q` | Failed | System Python does not have `pytest` installed |
| `python -m pytest tests/test_docs_contract.py -q` | Failed | System Python does not have `pytest` installed |
| `.\.venv\Scripts\python.exe -m pytest --version` | Passed | Reported `pytest 9.0.3` |
| `.\.venv\Scripts\python.exe -m pytest --collect-only -q` | Passed | Collected 12 tests |
| `.\.venv\Scripts\python.exe -m pytest tests/test_docs_contract.py -q` | Passed | `1 passed in 0.01s` |
| `.\.venv\Scripts\python.exe -m pytest -q` | Failed | `2 passed, 10 errors in 1.40s`; all errors came from Docker-backed PostgreSQL setup |

## Collection Snapshot

- Total collected tests: 12
- Passing without Docker: 2
- Failing in full-suite execution: 10
- Dominant failure mode: `docker compose up -d postgres` from `tests/conftest.py` could not connect to the Docker Desktop Linux engine on this Windows machine

## Coverage

- Coverage status: unavailable
- Reason:
  - `scripts/testing/measure-coverage.mjs` is missing
  - no repo-owned coverage command or committed coverage configuration was detected during this audit

## Blockers And Unavailable Areas

- Docker was unavailable during the audit, so the PostgreSQL-backed integration suite could not run to assertion completion.
- The required helper scripts under `scripts/testing/` are missing, so automated discovery, coverage measurement, and gap summarization are not currently runnable.
- The system Python at `C:\Users\Pavel\AppData\Local\Programs\Python\Python310\python.exe` does not include `pytest`; the repo-local `.venv` must be used instead.
