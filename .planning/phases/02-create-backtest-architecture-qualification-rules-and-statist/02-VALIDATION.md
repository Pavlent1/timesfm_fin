---
phase: 02
slug: create-backtest-architecture-qualification-rules-and-statist
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-14
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` |
| **Config file** | none |
| **Quick run command** | `python -m pytest -q tests/test_backtest_metrics.py tests/test_postgres_backtest.py tests/test_crypto_minute_backtest.py tests/test_script_wrappers.py tests/test_docs_contract.py` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest -q` against the smallest touched Phase 2 target, or the full quick command when a task crosses metric/storage/runtime boundaries.
- **After every plan wave:** Run `python -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | BT-03, BT-05 | T-02-01 | Metric formulas classify overshoot and undershoot exactly as the locked Phase 2 rules require | unit | `python -m pytest -q tests/test_backtest_metrics.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | BT-03 | T-02-02 | Reusable metric helpers emit normalized deviation and signed percent outputs without runtime-specific duplication | unit | `python -m pytest -q tests/test_backtest_metrics.py -k normalized` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | BT-01, BT-02, BT-04 | T-02-03 | PostgreSQL schema stores run/window/step facts and exposes a queryable per-step stats view | integration | `python -m pytest -q tests/test_postgres_backtest.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | BT-01, BT-04 | T-02-04 | Bootstrap and helper code apply all checked-in schema files and write reproducible run metadata | integration | `python -m pytest -q tests/test_postgres_backtest.py -k bootstrap` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | BT-01, BT-04 | T-02-05 | Runtime reads/writes PostgreSQL data through shared helpers and no longer depends on SQLite | integration | `python -m pytest -q tests/test_crypto_minute_backtest.py` | ✅ existing file | ⬜ pending |
| 02-03-02 | 03 | 2 | BT-05 | T-02-06 | Wrapper and docs describe PostgreSQL as canonical and pass the correct container/database wiring | contract | `python -m pytest -q tests/test_script_wrappers.py tests/test_docs_contract.py` | ✅ existing files | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_backtest_metrics.py` - metric semantics contract coverage for normalized deviation and overshoot rules
- [ ] `tests/test_postgres_backtest.py` - PostgreSQL schema, helper, and stats-view coverage
- [ ] Extend `tests/test_crypto_minute_backtest.py` for PostgreSQL-backed runtime behavior
- [ ] Extend `tests/test_script_wrappers.py` for PostgreSQL env wiring and SQLite removal
- [ ] Extend `tests/test_docs_contract.py` so README and `db/README.md` enforce the new PostgreSQL-backed operator path

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dockerized wrapper can reach the local PostgreSQL service from the container runtime | BT-01, BT-04 | Local Docker networking behavior varies across Windows, WSL, and Linux host setups | Start `docker compose up -d postgres`, run the documented wrapper command, and confirm the backtest writes rows into PostgreSQL rather than a local SQLite file |
| Per-step stats output is readable enough for an operator to inspect horizon-distance behavior quickly | BT-02 | Automated tests can pin schema and row values, but not report readability | Query the documented stats view for one run and confirm the output clearly shows step index, mean deviation, stddev, and overshoot/undershoot counts |

---

## Validation Sign-Off

- [ ] All tasks have automated verify commands or are covered by Wave 0 additions
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all missing Phase 2 references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter before phase completion

**Approval:** pending
