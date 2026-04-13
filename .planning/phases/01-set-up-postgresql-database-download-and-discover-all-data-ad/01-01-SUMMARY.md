---
phase: 01-set-up-postgresql-database-download-and-discover-all-data-ad
plan: "01"
subsystem: database
tags: [postgres, docker, psycopg, pytest]
requires: []
provides:
  - Compose-managed PostgreSQL 18.3 foundation for the repository
  - Checked-in Phase 1 schema bootstrap for assets, series, ingestion runs, and observations
  - Shared psycopg connection helpers and reusable pytest fixtures
affects: [ingestion, discovery, materialization, testing]
tech-stack:
  added: [postgres:18.3-bookworm, psycopg[binary]==3.3.3, pytest==9.0.3]
  patterns: [repo-owned compose database, checked-in SQL bootstrap, shared PostgreSQL fixtures]
key-files:
  created:
    - compose.yaml
    - db/init/001_phase1_schema.sql
    - src/postgres_dataset.py
    - src/bootstrap_postgres.py
    - tests/conftest.py
    - tests/test_db_connection.py
    - tests/test_schema_bootstrap.py
  modified:
    - requirements.inference.txt
    - requirements.dev.txt
key-decisions:
  - "Keep PostgreSQL access on direct psycopg helpers instead of introducing an ORM in Phase 1."
  - "Use a checked-in init SQL file plus a bootstrap CLI so schema setup works on first container boot and on reruns."
patterns-established:
  - "Database scripts import shared connection defaults from src/postgres_dataset.py."
  - "Phase 1 database tests create isolated databases off the shared compose service instead of mutating the primary DB."
requirements-completed: [DB-01, DB-02, DB-03]
duration: 18min
completed: 2026-04-13
---

# Phase 1: Plan 01 Summary

**Compose-backed PostgreSQL 18 foundation with checked-in schema bootstrap, shared psycopg helpers, and reusable database contract tests**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-13T16:00:00Z
- **Completed:** 2026-04-13T16:18:00Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Added the repo-owned PostgreSQL runtime path with a pinned `postgres:18.3-bookworm` Compose service.
- Checked in the Phase 1 schema for assets, logical series, ingestion provenance, and idempotent observation storage.
- Established shared psycopg helpers plus reusable pytest fixtures so later plans can test against isolated PostgreSQL databases.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the Phase 1 PostgreSQL test harness** - `8b7ce7f` (`test(phase-01): add postgres foundation test harness`)
2. **Task 2: Implement the compose-backed PostgreSQL foundation** - `443fb6f` (`feat(phase-01): add postgres compose bootstrap`)

**Plan metadata:** pending

## Files Created/Modified

- `compose.yaml` - Defines the pinned PostgreSQL service, volume, port binding, and health check.
- `db/init/001_phase1_schema.sql` - Bootstraps the Phase 1 schema and indexes.
- `src/postgres_dataset.py` - Holds shared settings, connection, wait, and schema-apply helpers.
- `src/bootstrap_postgres.py` - Provides the operator-facing schema bootstrap CLI.
- `tests/conftest.py` - Creates the reusable compose-backed PostgreSQL fixtures and isolated test databases.
- `tests/test_db_connection.py` - Locks the shared connection contract.
- `tests/test_schema_bootstrap.py` - Locks the required tables, types, and uniqueness key.

## Decisions Made

- Used direct psycopg connections and checked-in SQL because the repo is script-oriented and did not need ORM or migration-tool overhead in this phase.
- Mounted the checked-in SQL into `docker-entrypoint-initdb.d` and kept a separate bootstrap CLI for reruns against an existing database.

## Deviations from Plan

### Auto-fixed Issues

**1. Postgres 18 volume layout**
- **Found during:** Task 2 (Compose validation)
- **Issue:** The initial volume target used the pre-18 data path and caused the `postgres:18.3-bookworm` container to exit during startup.
- **Fix:** Updated the persistent volume target from `/var/lib/postgresql/data` to `/var/lib/postgresql` so the image can use its PostgreSQL 18 directory layout.
- **Files modified:** `compose.yaml`
- **Verification:** `docker compose config` succeeded, the container reached `healthy`, and the Wave 1 pytest suite passed against the live database.
- **Committed in:** `443fb6f`

---

**Total deviations:** 1 auto-fixed
**Impact on plan:** Required for correctness. No scope creep.

## Issues Encountered

- PostgreSQL 18 image startup failed on the first Compose attempt because of the older volume mount convention. The fix was applied immediately and validated against the live container.

## User Setup Required

None - no external service configuration required beyond Docker being available locally.

## Next Phase Readiness

- Shared PostgreSQL helpers, schema, and test fixtures are in place for ingestion and provenance work.
- The live compose service is healthy and the database contract tests are green, so Plan `01-02` can build directly on this foundation.

---
*Phase: 01-set-up-postgresql-database-download-and-discover-all-data-ad*
*Completed: 2026-04-13*
