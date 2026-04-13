---
phase: 01
slug: set-up-postgresql-database-download-and-discover-all-data-ad
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-13
---

# Phase 01 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` |
| **Config file** | none - Wave 0 installs and configures if needed |
| **Quick run command** | `python -m pytest -q tests/test_phase1_postgres.py` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~30 seconds once the Phase 1 test suite exists |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest -q tests/test_phase1_postgres.py` or the smallest touched Phase 1 test target.
- **After every plan wave:** Run `python -m pytest -q`.
- **Before `/gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 30 seconds for the quick Phase 1 checks.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-W0-DB | W0 | 0 | DB-01, DB-02 | T-01-01 | PostgreSQL bootstrap succeeds and project code can connect without ad hoc SQL steps | integration | `python -m pytest -q tests/test_db_connection.py tests/test_schema_bootstrap.py` | ❌ W0 | ⬜ pending |
| 01-W0-ING | W0 | 0 | ING-01, ING-02, ING-03 | T-01-02 | Ingestion records provenance and remains idempotent on rerun | integration | `python -m pytest -q tests/test_binance_ingest.py tests/test_provenance.py` | ❌ W0 | ⬜ pending |
| 01-W0-DISC | W0 | 0 | DISC-01, DISC-02, DISC-03 | T-01-03 | Discovery, filtering, sorting, and docs contracts stay verifiable | integration/smoke | `python -m pytest -q tests/test_discovery_cli.py tests/test_docs_contract.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_db_connection.py` - verify compose-backed connection behavior
- [ ] `tests/test_schema_bootstrap.py` - verify schema bootstrap and required tables/indexes
- [ ] `tests/test_binance_ingest.py` - verify import behavior and rerun idempotence
- [ ] `tests/test_provenance.py` - verify ingestion-run provenance and coverage metadata
- [ ] `tests/test_discovery_cli.py` - verify inventory, filtering, and sorting output
- [ ] `tests/test_docs_contract.py` - verify documented commands and schema workflow remain accurate
- [ ] `tests/conftest.py` - shared PostgreSQL fixtures or container-aware setup helpers
- [ ] install `pytest` and any Phase 1 test dependencies in the active environment

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker daemon can start the PostgreSQL service on the developer machine | DB-01 | Current environment evidence shows Docker CLI is present but the daemon was unavailable during research | Start the documented Docker service, run the documented bootstrap command, confirm the service stays healthy and accepts a project connection |
| CLI discovery output is understandable for a human operator | DISC-01, DISC-02, DISC-03 | Automated tests can validate fields and ordering, but readability still needs one human pass | Run the discovery command against sample data, confirm the columns and summaries make the dataset structure obvious without reading SQL |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for the quick checks
- [ ] `nyquist_compliant: true` set in frontmatter before phase completion

**Approval:** pending
