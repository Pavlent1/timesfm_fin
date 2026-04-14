---
artifact: global-autotest-plan
status: ready_for_execute
updated: 2026-04-13
scope:
  - src/
  - configs/
  - scripts/
execution_model: wave_based
based_on:
  - AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml
  - AgentHelper/ProjectFiles/TestAutomation/TEST_AUDIT.md
  - AgentHelper/ProjectFiles/TestAutomation/TEST_BASELINE.md
  - AgentHelper/ProjectFiles/TestAutomation/TEST_INVENTORY.md
---

# Global Automated Test Plan

## Status

- Plan status: `ready_for_execute`
- Requested scope: whole approved codebase (`src/`, `configs/`, `scripts/`)
- Preferences state used for planning: `actionable` with conservative defaults still open for CI thresholds, CI stages, and future mocking policy
- Audit freshness check: verified on 2026-04-13 by re-running the helper script entrypoints; `scripts/testing/discover-test-landscape.mjs` and `scripts/testing/summarize-test-gaps.mjs` still fail with `MODULE_NOT_FOUND`
- Current execution constraint: `scripts/precommit-checks.mjs` still requires Docker before running the full pytest suite because most existing PostgreSQL tests share the same Compose-backed fixture

## Planning Decisions Locked For Execution

- No browser or Playwright E2E wave is planned. The current repository shape is CLI-first and the saved preferences do not approve an E2E runner.
- Standardize future pytest layering around explicit markers: `unit`, `contract`, `integration`, and `docker`. The non-Docker reusable subset should be selectable with `-m "not docker"`.
- Keep the repo-managed pre-commit full-suite gate unchanged unless the user later revisits test preferences. This roadmap adds smaller runnable subsets; it does not silently downgrade the confirmed full-suite gate.
- Treat the legacy JAX/PAX training stack as intentionally light-tested for now. Prioritize deterministic helpers, CLI contracts, and data-path safety over real checkpoint execution.

## Prioritization Basis

This wave order is driven by:

- user-facing risk in the CLI-first forecast, evaluation, and backtest flows
- business-critical logic risk in shared Binance ingestion and PostgreSQL bootstrap paths
- failure-path risk from a single Docker outage masking most collected test signal
- measured gap size from the current audit and inventory
- framework readiness in the existing `pytest` suite
- maintenance cost and execution speed for early wins
- flake risk from environment-coupled tests

## Wave Overview

| Wave | Status | Scope | Why it matters now | Preferred layer | Depends on | Primary validation gate |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `pending` | Test automation tooling, pytest markers, and the always-runnable subset | The helper workflow and most quick feedback loops are blocked until discovery, gap reporting, and a non-Docker subset exist | Tooling + unit/contract | None | `node scripts/testing/discover-test-landscape.mjs --markdown` and `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"` |
| 2 | `pending` | Shared adapters and bootstrap CLI | Highest-risk missing regressions are in `src/binance_market_data.py` and `src/bootstrap_postgres.py` and can be covered without Docker | Unit + contract | Wave 1 | Targeted pytest files for market-data and bootstrap paths |
| 3 | `pending` | PostgreSQL workflow contracts and Docker-backed integration suite | Phase 1 data workflows are currently the newest implemented surface and are still all-or-nothing when Docker setup fails | Contract + integration | Wave 1 | Docker-marked PostgreSQL pytest suite and `node scripts/precommit-checks.mjs` in a Docker-ready environment |
| 4 | `pending` | Forecast, evaluation, crypto backtest, and wrapper safety net | The repo's core published CLI value still sits largely outside automated coverage | Unit + contract smoke | Waves 1-2 | Targeted pytest suites for `run_forecast`, `evaluate_forecast`, `crypto_minute_backtest`, and script wrappers |
| 5 | `pending` | Coverage reporting, audit refresh, and explicit deferrals | The roadmap needs a measurable stop point and updated artifacts after the major gaps close | Tooling + documentation | Waves 1-4 | Coverage command plus refreshed audit artifacts |

## Wave Details

### Wave 1: Restore Test Tooling And Create A Runnable Non-Docker Subset

- Status: `pending`
- Scope:
  - `scripts/testing/discover-test-landscape.mjs`
  - `scripts/testing/measure-coverage.mjs`
  - `scripts/testing/summarize-test-gaps.mjs`
  - pytest marker/config support for `unit`, `contract`, `integration`, `docker`
  - existing `tests/` files and `scripts/precommit-checks.mjs` only where needed to expose stable commands
  - refreshed `TEST_AUDIT.md`, `TEST_BASELINE.md`, and `TEST_INVENTORY.md`
- Why it matters now:
  - the helper planning workflow cannot measure or summarize current gaps automatically
  - the current suite offers almost no reusable signal when Docker is unavailable
  - every later wave benefits from having durable discovery, coverage, and gap reports
- Preferred test layer: tooling plus fast unit/contract checks
- Suggested execution scopes:
  - Scope A: `scripts/testing/` helper restoration
  - Scope B: pytest marker/config split and stable non-Docker selector
  - Scope C: audit artifact refresh after the first two scopes are green
- Acceptance criteria:
  - `discover-test-landscape`, `measure-coverage`, and `summarize-test-gaps` all exist under `scripts/testing/` and run successfully from the repo root
  - a stable pytest selector exists for always-runnable checks and uses `-m "not docker"`
  - the non-Docker subset passes without requiring a Docker daemon
  - the saved audit, baseline, and inventory reflect the new commands and no longer depend on manual narration for basic test landscape discovery
- Validation commands:
  - `node scripts/testing/discover-test-landscape.mjs --markdown`
  - `node scripts/testing/measure-coverage.mjs --markdown`
  - `node scripts/testing/summarize-test-gaps.mjs --markdown`
  - `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
- Dependencies or blockers:
  - No dependency to start
  - Do not relax the full-suite pre-commit gate here unless test preferences are explicitly updated in a separate decision

### Wave 2: Add Direct Coverage For Shared Market-Data And Bootstrap Paths

- Status: `pending`
- Scope:
  - `src/binance_market_data.py`
  - `src/bootstrap_postgres.py`
  - supporting pure branches in `src/postgres_dataset.py` only if needed for stable assertions
  - new targeted pytest files under `tests/`
- Why it matters now:
  - these files contain the highest-value uncovered behavior called out by the audit
  - both surfaces can be tested deterministically without TimesFM, PostgreSQL containers, or live network calls
  - they protect the Phase 1 data foundation from regressions in shared adapters and CLI wiring
- Preferred test layer: unit plus CLI contract tests
- Suggested execution scopes:
  - Scope A: Binance pagination, retry, malformed-response, and stalled-cursor tests
  - Scope B: PostgreSQL bootstrap argument parsing, wait handling, and schema-call tests
- Acceptance criteria:
  - `src/binance_market_data.py` has direct tests for HTTP 429 retry handling, malformed payload rejection, duplicate timestamp de-duplication, and stalled-cursor protection
  - `src/bootstrap_postgres.py` has direct tests for argument defaults, `--skip-wait`, schema path plumbing, and main-command collaborator calls
  - these tests run without Docker and without real network traffic
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_binance_market_data.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_bootstrap_postgres.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
- Dependencies or blockers:
  - Depends on Wave 1 marker/config support so the new tests land in the fast reusable subset

### Wave 3: Harden PostgreSQL Workflow Contracts And Docker-Backed Integration

- Status: `pending`
- Scope:
  - `tests/conftest.py`
  - existing Phase 1 PostgreSQL tests:
    - `tests/test_db_connection.py`
    - `tests/test_schema_bootstrap.py`
    - `tests/test_binance_ingest.py`
    - `tests/test_discovery_cli.py`
    - `tests/test_materialize_dataset.py`
    - `tests/test_provenance.py`
  - command-level contract checks for:
    - `src/bootstrap_postgres.py`
    - `src/postgres_ingest_binance.py`
    - `src/postgres_discover_data.py`
    - `src/postgres_verify_data.py`
    - `src/postgres_materialize_dataset.py`
- Why it matters now:
  - Phase 1 is the latest implemented milestone and the current test investment is already concentrated here
  - one infrastructure failure currently masks all assertion-level signal for the database-backed suite
  - the repo-managed pre-commit gate depends on this suite being diagnosable and trustworthy
- Preferred test layer: contract plus Docker-backed integration
- Suggested execution scopes:
  - Scope A: shared fixture diagnostics and marker hygiene
  - Scope B: bootstrap/ingest/provenance integration checks
  - Scope C: discovery/verify/materialize integration and CLI contract checks
- Acceptance criteria:
  - Docker-backed tests are explicitly marked and can be run separately from the fast subset
  - fixture failures report clear infrastructure errors instead of obscuring which layer is failing
  - the documented Phase 1 CLI flow has dedicated contract or smoke coverage in addition to the raw DB-behavior assertions
  - `node scripts/precommit-checks.mjs` succeeds in a Docker-capable environment
- Validation commands:
  - `docker info`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_db_connection.py tests/test_schema_bootstrap.py tests/test_binance_ingest.py tests/test_discovery_cli.py tests/test_materialize_dataset.py tests/test_provenance.py -q -m "docker"`
  - `node scripts/precommit-checks.mjs`
- Dependencies or blockers:
  - Depends on Wave 1
  - Blocked on a Docker-ready execution environment for final validation

### Wave 4: Add Deterministic Coverage For Forecast, Evaluation, And Crypto Backtest Flows

- Status: `pending`
- Scope:
  - `src/run_forecast.py`
  - `src/evaluate_forecast.py`
  - `src/crypto_minute_backtest.py`
  - `scripts/run_crypto_backtest.ps1`
  - `scripts/setup_windows.ps1` where lightweight wrapper or argument-contract checks are practical
- Why it matters now:
  - these files define the repository's core published user workflows
  - the audit found no direct automated coverage for the forecast, evaluation, or crypto backtest surfaces
  - deterministic helper and contract tests here provide high user-facing protection without requiring real checkpoint downloads
- Preferred test layer: unit plus contract smoke
- Suggested execution scopes:
  - Scope A: `run_forecast` input validation, CSV/Yahoo loading, and future-index behavior
  - Scope B: `evaluate_forecast` metric helpers and rolling-window logic
  - Scope C: `crypto_minute_backtest` batching, persistence, and metric helpers
  - Scope D: PowerShell wrapper argument and command-construction contracts
- Acceptance criteria:
  - `run_forecast`, `evaluate_forecast`, and `crypto_minute_backtest` each have direct deterministic coverage for their highest-risk helper logic
  - external boundaries (`timesfm`, Yahoo Finance, Binance HTTP, SQLite filesystem paths) are stubbed or redirected to temporary resources
  - wrapper tests protect the documented Windows/Docker entrypoints without requiring actual model execution
  - no wave-level validation command downloads a real TimesFM checkpoint
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_forecast.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_evaluate_forecast.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_crypto_minute_backtest.py -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_script_wrappers.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -q -m "not docker"`
- Dependencies or blockers:
  - Depends on Waves 1 and 2
  - TimesFM-heavy branches may need seam creation or deferred-import testing patterns to stay lightweight

### Wave 5: Re-Measure Coverage, Refresh Audit Artifacts, And Record Explicit Deferrals

- Status: `pending`
- Scope:
  - refreshed `TEST_AUDIT.md`, `TEST_BASELINE.md`, and `TEST_INVENTORY.md`
  - updated coverage reporting from `scripts/testing/measure-coverage.mjs`
  - `GLOBAL_AUTOTEST_PLAN.md` adjustments if scope or ordering changed during execution
  - explicit deferred coverage note for legacy training and unapproved E2E work
- Why it matters now:
  - the roadmap needs a measurable stopping point after the main coverage waves land
  - later sessions need refreshed artifacts instead of relying on the initial 2026-04-13 baseline
  - unresolved preference questions about CI stages and coverage thresholds should remain visible instead of being silently assumed
- Preferred test layer: tooling plus documentation
- Suggested execution scopes:
  - Scope A: coverage/baseline measurement refresh
  - Scope B: audit and inventory refresh
  - Scope C: deferral and remaining-risk documentation
- Acceptance criteria:
  - coverage reporting runs from the repo root and produces a readable baseline for the current test stack
  - the audit artifacts reflect the actual post-wave test landscape instead of the original bootstrap state
  - deferred areas are explicit:
    - legacy JAX/PAX training and evaluation remain intentionally light-tested
    - no browser E2E runner is approved
    - CI-stage enforcement and hard coverage thresholds still require user confirmation in preferences
- Validation commands:
  - `node scripts/testing/discover-test-landscape.mjs --markdown`
  - `node scripts/testing/measure-coverage.mjs --markdown`
  - `node scripts/testing/summarize-test-gaps.mjs --markdown`
  - `.\.venv\Scripts\python.exe -m pytest --collect-only -q`
- Dependencies or blockers:
  - Depends on Waves 1-4
  - Do not invent CI thresholds or nightly policies here; escalate those back through `helper-test-preferences`

## Sequencing Notes

- Start with Wave 1 even if Wave 2 feels smaller. The repo needs stable discovery, measurement, and a runnable subset before execution can stay efficient.
- Wave 3 must run in a Docker-capable environment for final validation, but its non-Docker prep work can start earlier.
- Wave 4 deliberately stays out of real checkpoint execution. If lightweight deterministic seams are impossible for a sub-area, record that blocker rather than silently expanding into heavyweight integration work.
- No separate E2E wave is included. CLI contract and smoke coverage is the approved substitute for this repo state.

## Deferred Until Preferences Change Or Scope Expands

- Browser/E2E tooling such as Playwright or Cypress
- Hard coverage thresholds or CI-stage enforcement beyond the existing repo-managed pre-commit hook
- Heavyweight end-to-end validation of the legacy training stack against real JAX/PAX/TimesFM environments

## Handoff

- Recommended first execution command: `helper-test-execute-plan`
- Recommended starting wave: `Wave 1`
- If the user wants the fastest risk reduction after Wave 1, continue with `Wave 2`
