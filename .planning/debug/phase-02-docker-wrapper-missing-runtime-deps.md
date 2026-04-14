---
status: resolved
trigger: "Investigate issue: phase-02-docker-wrapper-missing-runtime-deps"
created: 2026-04-14T19:05:00Z
updated: 2026-04-14T21:48:00Z
---

## Current Focus

hypothesis: Resolved.
test: Fixed by aligning the Docker image with the shared runtime requirements and validating the real wrapper path against a full-coverage PostgreSQL day.
expecting: Fixed.
next_action: none

## Symptoms

expected: Running `scripts/run_crypto_backtest.ps1` should start the containerized PostgreSQL-backed backtest runtime, connect to PostgreSQL via `host.docker.internal`, and persist run/window/step rows without using SQLite.
actual: The wrapper launches the container, but `src/crypto_minute_backtest.py` crashes immediately inside the container before any backtest run is stored.
errors: `ModuleNotFoundError: No module named 'psycopg'` from inside the containerized runtime. A host-side fallback also cannot run the runtime because the local Python environment lacks the TimesFM runtime dependencies (`jax` / `torch`).
reproduction: From repo root on Windows PowerShell, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\run_crypto_backtest.ps1 -SkipBuild -Day 2024-04-01 -ContextLen 64 -HorizonLen 8 -Stride 8 -BatchSize 1 -MaxWindows 1 -Backend cpu`.
started: The failure was observed during Phase 2 UAT after the PostgreSQL-backed runtime migration was already merged. Phase 2 summaries claim the wrapper/runtime path is ready, but the real UAT run exposed the container dependency mismatch.

## Eliminated

## Evidence

- timestamp: 2026-04-14T19:06:00Z
  checked: `.planning/debug/knowledge-base.md`
  found: The debug knowledge base file does not exist in this repository.
  implication: No prior resolved debug pattern is available to shortcut this investigation.

- timestamp: 2026-04-14T19:06:00Z
  checked: `Dockerfile` and `requirements.inference.txt`
  found: `requirements.inference.txt` includes `psycopg[binary]==3.3.3`, but `Dockerfile` installs an inline package list and omits `psycopg`.
  implication: Rebuilding the image from the current Dockerfile still produces a container that cannot import `psycopg`.

- timestamp: 2026-04-14T19:06:00Z
  checked: `scripts/run_crypto_backtest.ps1`
  found: The wrapper always runs the built image with `--entrypoint python` and executes `src/crypto_minute_backtest.py` inside the container.
  implication: The crash occurs on the supported Docker wrapper path itself, not on an alternate host fallback path.

- timestamp: 2026-04-14T19:06:00Z
  checked: `src/crypto_minute_backtest.py`
  found: The module imports `psycopg` at top level before any runtime setup or backtest persistence logic runs.
  implication: Missing `psycopg` causes an immediate startup failure before the backtest can create PostgreSQL run/window/step rows.

- timestamp: 2026-04-14T19:07:00Z
  checked: `common-bug-patterns.md`
  found: The failure matches the Environment/Config missing-dependency pattern.
  implication: The likely fix is to correct the container build inputs rather than the PostgreSQL runtime code.

## Resolution

root_cause: The supported Docker image for `scripts/run_crypto_backtest.ps1` is built from a stale inline `pip install` list in `Dockerfile` that omits `psycopg`, while the Phase 2 PostgreSQL-backed runtime imports `psycopg` at module load time.
fix:
verification:
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_script_wrappers.py -x`
- `docker build -t timesfm-fin .`
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_crypto_backtest.ps1 -SkipBuild -Day 2026-04-13 -ContextLen 64 -HorizonLen 8 -Stride 8 -BatchSize 1 -MaxWindows 1 -Backend cpu`
- Queried `market_data.backtest_runs` and `market_data.backtest_step_stats_vw` for `run_id = 1`
fix: Updated `Dockerfile` to install `requirements.inference.txt` while keeping `timesfm[pax]==1.3.0`, and added a contract test in `tests/test_script_wrappers.py` that asserts the Docker image consumes the shared runtime requirements.
files_changed: [Dockerfile, tests/test_script_wrappers.py]
