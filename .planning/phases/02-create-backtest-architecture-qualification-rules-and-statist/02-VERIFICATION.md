---
phase: 02-create-backtest-architecture-qualification-rules-and-statist
verified: 2026-04-14T15:41:17.2406097Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run the Docker wrapper against a real local PostgreSQL service"
    expected: "The container reaches PostgreSQL through host.docker.internal, inserts backtest_runs/backtest_windows/backtest_prediction_steps rows, and does not create a SQLite backtest store."
    why_human: "This depends on the operator's local Docker and host-network setup; verification here did not start services."
  - test: "Inspect one stored run through market_data.backtest_step_stats_vw"
    expected: "The per-step output is readable enough for an operator to inspect horizon-distance behavior quickly."
    why_human: "Automated tests verify schema and numeric correctness, but not operator readability."
---

# Phase 2: Create backtest architecture, qualification rules, and statistics collection Verification Report

**Phase Goal:** Replace the SQLite-only crypto backtest experiment store with a PostgreSQL-backed architecture that persists run, window, and per-step prediction facts and exposes queryable per-horizon statistics using the locked Phase 2 metric semantics.
**Verified:** 2026-04-14T15:41:17.2406097Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | The backtest workflow writes canonical run, window, and per-step prediction facts to PostgreSQL through the shared repo connection path. | VERIFIED | `src/crypto_minute_backtest.py:193,301,543,709` loads candles via PostgreSQL, persists live fetches back into PostgreSQL, and writes runs/windows/steps through `src/postgres_backtest.py:9,69,102`; persistence is covered by `tests/test_crypto_minute_backtest.py:120,141,269` and `tests/test_postgres_backtest.py:163`. |
| 2 | PostgreSQL exposes direct per-step aggregate statistics for normalized deviation and overshoot/undershoot behavior across a run. | VERIFIED | `db/init/002_phase2_backtest_schema.sql:57` defines `market_data.backtest_step_stats_vw`; `src/postgres_backtest.py:147` queries it directly; `tests/test_postgres_backtest.py:204` verifies grouped per-step stats for one run. |
| 3 | Stored metrics and automated tests match the locked formulas and context-relative classification rules from Phase 2 context. | VERIFIED | `src/backtest_metrics.py:20,25,43,64` implements normalized deviation, context-relative overshoot classification, signed deviation, and reusable step packaging; `tests/test_backtest_metrics.py` locks upward/downward semantics; `src/crypto_minute_backtest.py:447` uses `build_step_metrics` instead of duplicating formulas. |
| 4 | The shared bootstrap path applies the Phase 2 schema alongside the Phase 1 schema from checked-in SQL. | VERIFIED | `src/postgres_dataset.py:61,108` collects `db/init/*.sql` in lexical order and applies them during bootstrap; `src/bootstrap_postgres.py:68` uses that shared path; `tests/test_postgres_backtest.py:137` and `tests/test_schema_bootstrap.py:4` verify both Phase 1 and Phase 2 objects are created. |
| 5 | The CLI wrapper and repository docs describe the PostgreSQL-backed backtest flow and no longer present SQLite as the canonical store. | VERIFIED | `scripts/run_crypto_backtest.ps1:13,56,57` injects PostgreSQL env vars and host-gateway wiring with CPU as the default backend; `README.md:148,157,174,182` and `db/README.md:61,104` document the PostgreSQL flow and stats view; `tests/test_script_wrappers.py:24,100` and `tests/test_docs_contract.py:9` enforce the contract and reject stale SQLite guidance. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/backtest_metrics.py` | Phase 2 metric formulas and classification helpers | VERIFIED | Exposes `normalized_deviation_pct`, `classify_overshoot`, `signed_deviation_pct`, and `build_step_metrics`; no runtime or DB coupling. |
| `tests/test_backtest_metrics.py` | Locked formula and classification contract tests | VERIFIED | Covers literal normalized deviation formula, upward/downward overshoot rules, exact-match behavior, and signed deviation semantics. |
| `db/init/002_phase2_backtest_schema.sql` | Phase 2 run/window/step tables and stats view | VERIFIED | Defines `backtest_runs`, `backtest_windows`, `backtest_prediction_steps`, `backtest_step_stats_vw`, and the composite run/window integrity constraint. |
| `src/postgres_dataset.py` | Shared lexical bootstrap and PostgreSQL connection path | VERIFIED | `schema_sql_paths()` and `bootstrap_schema()` apply checked-in schema files in lexical order through the shared connection helper. |
| `src/postgres_backtest.py` | Shared parameterized persistence/query helpers | VERIFIED | Uses `%s` parameter placeholders for run/window/step inserts and for stats-view reads. |
| `src/crypto_minute_backtest.py` | PostgreSQL-backed runtime using shared metric/persistence helpers | VERIFIED | Reads Phase 1 candles from PostgreSQL, persists live fetches to PostgreSQL, computes Phase 2 per-step metrics, and saves runs/windows/steps through shared helpers. |
| `scripts/run_crypto_backtest.ps1` | Container wrapper with PostgreSQL wiring | VERIFIED | Passes `POSTGRES_*` env vars, `host.docker.internal`, and host-gateway wiring; no `--db-path` flag remains. |
| `README.md` and `db/README.md` | Operator docs for PostgreSQL backtest flow | VERIFIED | Show the canonical PostgreSQL-backed backtest path and direct inspection of `market_data.backtest_step_stats_vw`. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/bootstrap_postgres.py` | `db/init/*.sql` | `postgres_dataset.bootstrap_schema()` | WIRED | `src/bootstrap_postgres.py:68` calls the shared bootstrap; `src/postgres_dataset.py:61,108` resolves and applies all sibling SQL files. |
| `src/crypto_minute_backtest.py` | `src/backtest_metrics.py` | `build_step_metrics()` in backtest step loop | WIRED | Imported at `src/crypto_minute_backtest.py:13` and used at `:447` for every stored step. |
| `src/crypto_minute_backtest.py` | `src/postgres_backtest.py` | `create_backtest_run/create_backtest_window/insert_backtest_steps` | WIRED | Imported at `:16-19` and used in `save_backtest()` at `:551-578`. |
| `src/crypto_minute_backtest.py` | Phase 1 PostgreSQL candles | `connect_postgres()` + `load_frame_range()` SQL over `market_data.observations` | WIRED | `load_frame_range()` at `:193` reads Phase 1 observations; `main()` opens the shared PostgreSQL connection at `:709`. |
| `src/postgres_backtest.py` | `market_data.backtest_step_stats_vw` | `query_backtest_step_stats()` | WIRED | Query helper at `src/postgres_backtest.py:147` reads the view defined in `db/init/002_phase2_backtest_schema.sql:57`. |
| `scripts/run_crypto_backtest.ps1` | container runtime | `POSTGRES_*` env vars + `host.docker.internal` | WIRED | Wrapper passes `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `--add-host host.docker.internal:host-gateway`. |
| `README.md` / `db/README.md` | operator workflow | documented PostgreSQL backtest commands and SQL inspection query | WIRED | README points operators to PostgreSQL-backed backtests and the stats view; db docs describe the schema objects and inspection query. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/crypto_minute_backtest.py` historical mode | `frame` | `load_backtest_frame()` -> `load_frame_range()` SQL over `market_data.observations` | Yes | FLOWING |
| `src/crypto_minute_backtest.py` live mode | `frame` | `prepare_live_frame()` -> `fetch_binance_klines()` -> `persist_binance_rows()` -> reload from PostgreSQL | Yes | FLOWING |
| `src/postgres_backtest.py` stats query | `stats_rows` | `market_data.backtest_step_stats_vw` grouped over `market_data.backtest_prediction_steps` | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full repo validation stays green on the current tree | `.\.venv\Scripts\python.exe -m pytest -q` | `60 passed in 8.81s` | PASS |
| Bootstrap CLI exposes the shared lexical schema flow | `.\.venv\Scripts\python.exe src/bootstrap_postgres.py --help` | Help text confirms checked-in schema anchor file applies sibling `db/init/*.sql` in lexical order | PASS |
| Backtest CLI exposes PostgreSQL as the canonical runtime path | `.\.venv\Scripts\python.exe src/crypto_minute_backtest.py --help` | Help text shows PostgreSQL connection flags and no `--db-path` option | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BT-01` | `02-02`, `02-03` | User can run the crypto minute backtest with PostgreSQL as the canonical store for backtest runs, windows, and per-step prediction facts. | SATISFIED | Runtime uses PostgreSQL for historical reads and backtest persistence (`src/crypto_minute_backtest.py`, `src/postgres_backtest.py`); persistence contract covered by `tests/test_crypto_minute_backtest.py` and `tests/test_postgres_backtest.py`. |
| `BT-02` | `02-02` | User can query per-output-candle backtest statistics directly from PostgreSQL so horizon-distance behavior is inspectable without manual recomputation. | SATISFIED | SQL view `market_data.backtest_step_stats_vw` plus query helper `query_backtest_step_stats()` and stats-view tests. |
| `BT-03` | `02-01` | User can inspect overshoot and undershoot outcomes using the locked context-relative classification and signed percent deviation rules. | SATISFIED | `src/backtest_metrics.py` and `tests/test_backtest_metrics.py` implement and lock the context-relative classification and signed deviation semantics. Note: `.planning/REQUIREMENTS.md` still marks BT-03 as planned, so the traceability metadata lags the implementation evidence. |
| `BT-04` | `02-02`, `02-03` | User can reproduce a stored backtest result from recorded run metadata, model settings, and source data coverage. | SATISFIED | Run metadata persists model repo, backend, freq/context/horizon/stride/batch settings and actual loaded coverage in `market_data.backtest_runs`; regression coverage exists in `tests/test_crypto_minute_backtest.py:357` and persistence tests. |
| `BT-05` | `02-01`, `02-02`, `02-03` | User can rely on automated tests to catch regressions in backtest metric semantics and PostgreSQL persistence. | SATISFIED | Metric, schema/persistence, runtime, wrapper, docs, bootstrap, and full-suite validation all pass on the current tree. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| None detected | - | Scoped scan found no TODO/FIXME/placeholders, no live SQLite persistence path, and no empty or stubbed implementations in the verified Phase 02 files. Prior review warnings WR-01, WR-02, and WR-03 are fixed in code and covered by tests. | - | No blocker or warning anti-patterns remain in scope. |

### Human Verification Required

### 1. Docker Wrapper To Local PostgreSQL

**Test:** Start `docker compose up -d postgres`, ensure the Phase 1 Binance dataset exists, then run `.\scripts\run_crypto_backtest.ps1 -Day 2026-04-11`.
**Expected:** The container reaches PostgreSQL through `host.docker.internal`, the run writes rows into `market_data.backtest_runs`, `market_data.backtest_windows`, and `market_data.backtest_prediction_steps`, and no SQLite backtest store is created.
**Why human:** This depends on the operator's local Docker and host networking setup. Verification here did not start services.

### 2. Per-Step Stats Operator Readability

**Test:** After a real backtest run, query `SELECT * FROM market_data.backtest_step_stats_vw WHERE run_id = <run_id> ORDER BY step_index;`.
**Expected:** The output makes horizon-distance behavior easy to inspect, including step index, average normalized deviation, standard deviation, and overshoot/undershoot counts.
**Why human:** Automated checks verify correctness and presence, but not whether the output is operationally readable enough for the intended workflow.

### Gaps Summary

No blocking implementation gaps found. The Phase 02 code, schema, runtime, wrapper, docs, and automated tests satisfy the phase goal. Remaining work is limited to manual environment validation of Docker-to-PostgreSQL connectivity and operator readability of the stats output.

---

_Verified: 2026-04-14T15:41:17.2406097Z_
_Verifier: Claude (gsd-verifier)_
