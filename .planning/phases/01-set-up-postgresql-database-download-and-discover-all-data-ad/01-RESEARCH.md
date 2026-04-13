# Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization - Research

**Researched:** 2026-04-13 [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md]  
**Domain:** PostgreSQL-backed market-data ingestion, discovery, and CSV materialization for an existing CLI-first Python toolkit [VERIFIED: codebase grep]  
**Confidence:** MEDIUM [ASSUMED]

<user_constraints>
## User Constraints (from CONTEXT.md)

Copied verbatim from `.planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md`. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md]

### Locked Decisions
- **D-01:** Standardize on a local Docker-based PostgreSQL setup owned by the repository, with a YAML-based container definition rather than ad hoc manual setup.
- **D-02:** Phase 1 should provide one documented, repo-native setup path that project scripts can rely on from the supported local runtime story.
- **D-03:** Design the schema for multiple assets/symbols from the start rather than hard-coding a BTC-only structure.
- **D-04:** The initial stored data type is intentionally narrow: 1-minute candle close-price time-series data is enough for Phase 1.
- **D-05:** The first concrete ingestion workflow is a one-time script that downloads and stores about the past 1 year of Binance `BTCUSDT` 1-minute close-price data.
- **D-06:** The data layer must support storing different datasets such as multi-year BTC and SOL minute histories in the same system later, even though the first loader targets only Bitcoin.
- **D-07:** Ingestion must be rerunnable without creating duplicate observations or silently corrupting existing data, and it must preserve dataset provenance and coverage metadata.
- **D-08:** Dataset discovery in Phase 1 should be script-driven, not SQL-docs-only. Users should be able to inspect what data exists through project commands or scripts.
- **D-09:** Phase 1 must include scripts for data integrity verification because cleaner data is treated as directly important for better model and backtest results.
- **D-10:** Integrity verification must check at least duplicate timestamps, missing minute gaps, ordering problems, null values, out-of-range timestamps, and coverage summaries.
- **D-11:** Discovery/reporting should support filtering and sorting stored data by source, symbol, timeframe, and date range.
- **D-12:** Phase 1 must include a working path from PostgreSQL-backed data into later backtest and fine-tuning workflows; this should not stop at raw storage only.

### Claude's Discretion
- The exact first bridge from PostgreSQL into existing CSV-driven training/backtest code is left to the agent's discretion during planning.
- Favor the simplest reliable path that works in this codebase, whether that is a PostgreSQL-to-CSV/materialized dataset step, a reusable database extraction layer, or a direct PostgreSQL reader for one workflow.
- The initial implementation does not need to generalize beyond 1-minute close-price datasets as long as the schema is not painted into a corner for additional symbols later.

### Deferred Ideas (OUT OF SCOPE)
- Recurring scheduled refreshes into PostgreSQL are not the immediate target for this first one-time ingestion workflow.
- Real-time or streaming ingestion remains out of scope for v1.
- Broader candle fields or additional market-data shapes beyond 1-minute close-price series can come after the initial schema foundation is proven.
- Full first-class PostgreSQL-native forecasting/training execution across all existing workflows may extend beyond Phase 1, as long as this phase delivers a working bridge and does not block that path.
</user_constraints>

<phase_requirements>
## Phase Requirements

Descriptions copied from `.planning/REQUIREMENTS.md`. [VERIFIED: .planning/REQUIREMENTS.md]

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-01 | User can provision a PostgreSQL database and connect to it from the project runtime with one documented setup path. | `compose.yaml` + official `postgres` image + `psycopg` connection module + Windows/Docker wrapper recommendation [CITED: https://hub.docker.com/_/postgres] [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html] |
| DB-02 | User can create the required PostgreSQL schema for assets, observations, and dataset metadata without manual ad hoc SQL edits. | Init SQL mounted into `/docker-entrypoint-initdb.d/` plus explicit schema-apply command recommendation [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] |
| DB-03 | User can store financial time-series data in PostgreSQL with enough structure to query by symbol, source, timeframe, and date range. | Series catalog + ingestion runs + observations schema pattern and indexed filter columns [VERIFIED: codebase grep] [ASSUMED] |
| ING-01 | User can download or import the target market data into PostgreSQL through a repeatable project command or script. | Binance Klines pagination pattern + psycopg batch/COPY options [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints] [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] |
| ING-02 | User can rerun ingestion without creating duplicate rows or silently corrupting existing data. | Unique observation key + `INSERT ... ON CONFLICT` recommendation [CITED: https://www.postgresql.org/docs/18/sql-insert.html] |
| ING-03 | User can track where imported data came from, when it was loaded, and what date range it covers. | Separate ingestion-run provenance table with coverage fields and loader metadata [ASSUMED] |
| DISC-01 | User can inspect which symbols, sources, and date ranges are currently available in the PostgreSQL dataset. | Discovery query/view + CLI report recommendation [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [ASSUMED] |
| DISC-02 | User can sort and filter stored data by symbol, source, timeframe, and date so the dataset is easy to explore. | Aggregated discovery SQL with explicit `WHERE` + `ORDER BY` pattern [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [ASSUMED] |
| DISC-03 | User can understand the database schema and ingestion workflow from repository documentation without reverse-engineering the code. | README + schema diagram/table docs + command examples recommendation [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED] |
</phase_requirements>

## Summary

Phase 1 should not be planned as “swap SQLite for PostgreSQL” in one file. The current SQLite path is embedded inside `src/crypto_minute_backtest.py`, which already mixes CLI parsing, Binance HTTP fetches, persistence, metrics, and console output in one script. [VERIFIED: codebase grep] Phase 1 should instead establish a small PostgreSQL data layer with its own schema bootstrap, ingestion command, discovery command, integrity command, and CSV materialization command. [VERIFIED: codebase grep] [ASSUMED]

The lowest-risk stack for this repo is a Docker-managed PostgreSQL service defined in `compose.yaml`, initialized by checked-in SQL files, and accessed from Python with `psycopg` rather than an ORM. [CITED: https://hub.docker.com/_/postgres] [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] [CITED: https://pypi.org/project/psycopg/] This matches the repo’s existing script-oriented style, avoids forcing SQLAlchemy/Alembic into a flat CLI codebase on day one, and still gives you proper upserts, `COPY`, `timestamptz`, and durable indexing. [VERIFIED: codebase grep] [CITED: https://www.postgresql.org/docs/18/sql-insert.html] [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] [ASSUMED]

The first downstream bridge should be a deterministic PostgreSQL-to-CSV materialization command, not a repo-wide refactor of every model/backtest entrypoint to read PostgreSQL directly. [VERIFIED: codebase grep] [ASSUMED] The existing modeling surface already consumes CSV cleanly in `src/run_forecast.py`, `src/evaluate_forecast.py`, and the fine-tuning path still expects file-based datasets in `src/main.py` and `src/train.py`. [VERIFIED: codebase grep] Planning around an export/materialization step keeps Phase 1 inside scope while still satisfying the “working path into later backtest and fine-tuning workflows” decision. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [ASSUMED]

**Primary recommendation:** Use `compose.yaml` + `postgres:18.3-bookworm`, `psycopg[binary]==3.3.3`, a versioned SQL bootstrap, and four Phase 1 CLIs: `bootstrap-schema`, `ingest-binance`, `discover-data`, and `materialize-dataset`. [CITED: https://hub.docker.com/_/postgres] [CITED: https://pypi.org/project/psycopg/] [ASSUMED]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docker Official `postgres` image | `18.3-bookworm` or another pinned `18.3` tag, released 2026-02-26 [CITED: https://hub.docker.com/_/postgres] [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] | Repo-owned PostgreSQL service | Docker Hub documents `compose.yaml` usage, init environment variables, init scripts, and PostgreSQL 18-specific volume behavior. [CITED: https://hub.docker.com/_/postgres] |
| PostgreSQL server | `18.x current` [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] | Relational storage, indexing, upserts, date/time, discovery queries | Official docs give you `GENERATED AS IDENTITY`, `timestamptz`, `INSERT ... ON CONFLICT`, and `COPY`, which are the exact primitives Phase 1 needs. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [CITED: https://www.postgresql.org/docs/18/sql-insert.html] [CITED: https://www.postgresql.org/docs/18/sql-copy.html] |
| `psycopg[binary]` | `3.3.3`, released 2026-02-18 [CITED: https://pypi.org/project/psycopg/] | Python PostgreSQL adapter for scripts | Psycopg 3 is the current adapter for new development, keeps DB-API familiarity close to `sqlite3`, supports parameterized queries, batch inserts, and `Cursor.copy()`. [CITED: https://pypi.org/project/psycopg/] [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html] [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Docker Compose CLI | Installed locally as `v5.1.0`; use Compose v2 workflow [VERIFIED: local env] [CITED: https://hub.docker.com/_/postgres] | Bring up PostgreSQL with one documented repo-native command | Use for the locked Docker-based setup path and for mounting init SQL plus a persistent volume. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [CITED: https://hub.docker.com/_/postgres] [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] |
| `pytest` | `9.0.3`, released 2026-04-07 [CITED: https://pypi.org/project/pytest/] | Phase 1 validation harness | Use because the repo currently has no tests, and Phase 1 needs integration tests around schema bootstrap, ingestion idempotence, and discovery queries. [VERIFIED: codebase grep] [CITED: https://pypi.org/project/pytest/] |
| Existing `pandas` dependency | Repo pin is `>=2.2,<3.0` [VERIFIED: requirements.inference.txt] | Discovery reports and CSV materialization | Reuse it for sorted exports and summary tables instead of inventing a new reporting layer. [VERIFIED: codebase grep] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct `psycopg` + checked-in SQL bootstrap [ASSUMED] | SQLAlchemy `2.0.49` [CITED: https://pypi.org/project/SQLAlchemy/] | SQLAlchemy is mature and powerful, but this repo already uses direct SQL patterns and script entrypoints, so adding its abstraction layer in Phase 1 increases surface area more than it reduces risk. [VERIFIED: codebase grep] [CITED: https://pypi.org/project/SQLAlchemy/] [ASSUMED] |
| Checked-in SQL bootstrap + explicit schema command [ASSUMED] | Alembic `1.18.4` [CITED: https://pypi.org/project/alembic/] | Alembic is the standard SQLAlchemy migration tool and is worth adopting when schema churn grows, but Phase 1 only needs a first schema with reproducible bootstrap and a small number of tables. [CITED: https://pypi.org/project/alembic/] [ASSUMED] |
| Docker-managed PostgreSQL [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] | Native host PostgreSQL install [ASSUMED] | Native install conflicts with the locked Docker decision and creates a second setup path the phase explicitly does not want. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] |

**Installation:** Recommended Phase 1 additions. [ASSUMED]

```bash
docker compose up -d db
python -m pip install "psycopg[binary]==3.3.3" "pytest==9.0.3"
```

**Version verification:** `postgres` Docker Hub currently exposes `18.3` tags and PostgreSQL docs mark 18 as current. [CITED: https://hub.docker.com/_/postgres] [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] `psycopg` is at `3.3.3` on PyPI. [CITED: https://pypi.org/project/psycopg/] `pytest` is at `9.0.3` on PyPI. [CITED: https://pypi.org/project/pytest/]

## Architecture Patterns

### Recommended Project Structure

```text
compose.yaml                     # Repo-owned PostgreSQL service
db/
└── init/
    └── 001_schema.sql           # First-run bootstrap SQL mounted into the container
src/
├── postgres_db.py               # connect(), transactions, shared SQL helpers
├── ingest_binance_postgres.py   # one-time BTCUSDT 1m backfill command
├── discover_postgres_data.py    # coverage/filter/sort report command
├── validate_postgres_data.py    # duplicate/gap/null/order integrity checks
└── materialize_postgres_csv.py  # bridge into current CSV-driven workflows
scripts/
└── run_postgres_ingest.ps1      # optional Windows wrapper following current script style
``` 

This structure preserves the repo’s flat `src/` CLI pattern and keeps Docker/bootstrap artifacts outside `src/`. [VERIFIED: .planning/codebase/STRUCTURE.md] [ASSUMED]

### Pattern 1: Separate logical series from ingestion runs

**What:** Store one logical dataset/series row per `(source, symbol, timeframe)` and separate each load attempt into an ingestion-run table. [ASSUMED]  
**When to use:** Use this immediately because the phase requires rerunnable ingestion plus provenance, and a single observations table keyed only by a run id makes idempotence awkward. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED]

**Example:**

```sql
-- Adapted to Phase 1 from PostgreSQL identity/timestamptz capabilities.
CREATE TABLE market_data.series (
    series_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name text NOT NULL,
    symbol text NOT NULL,
    timeframe text NOT NULL,
    UNIQUE (source_name, symbol, timeframe)
);

CREATE TABLE market_data.ingestion_runs (
    ingestion_run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id bigint NOT NULL REFERENCES market_data.series(series_id),
    requested_start_utc timestamptz NOT NULL,
    requested_end_utc timestamptz NOT NULL,
    loaded_at_utc timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE market_data.observations (
    series_id bigint NOT NULL REFERENCES market_data.series(series_id),
    open_time_utc timestamptz NOT NULL,
    close_price double precision NOT NULL,
    ingestion_run_id bigint NOT NULL REFERENCES market_data.ingestion_runs(ingestion_run_id),
    PRIMARY KEY (series_id, open_time_utc)
);
```

Source basis: PostgreSQL 18 identity columns and `timestamptz`. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] The exact table names and `double precision` choice are Phase 1 recommendations, not an upstream standard. [ASSUMED]

### Pattern 2: Idempotent ingest with a unique observation key and upsert

**What:** Key each observation by logical series plus minute timestamp, then rerun ingestion with `INSERT ... ON CONFLICT`. [CITED: https://www.postgresql.org/docs/18/sql-insert.html]  
**When to use:** Use this for all Binance backfills and any future CSV imports in this repo. [ASSUMED]

**Example:**

```sql
INSERT INTO market_data.observations (
    series_id,
    open_time_utc,
    close_price,
    ingestion_run_id
)
VALUES ($1, $2, $3, $4)
ON CONFLICT (series_id, open_time_utc) DO UPDATE
SET close_price = EXCLUDED.close_price,
    ingestion_run_id = EXCLUDED.ingestion_run_id;
```

This relies on PostgreSQL’s deterministic `ON CONFLICT DO UPDATE` behavior and its recommendation to prefer unique index inference over hard-coded constraint names. [CITED: https://www.postgresql.org/docs/18/sql-insert.html]

### Pattern 3: Discovery and integrity as first-class CLI reports

**What:** Build discovery and validation as Python entrypoints that run SQL queries and print sortable summaries instead of telling users to inspect raw SQL tables manually. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [ASSUMED]  
**When to use:** Use this for `DISC-01`, `DISC-02`, and `D-09`/`D-10`. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md]

**Example:**

```python
import psycopg

query = """
SELECT
    s.source_name,
    s.symbol,
    s.timeframe,
    MIN(o.open_time_utc) AS data_start_utc,
    MAX(o.open_time_utc) AS data_end_utc,
    COUNT(*) AS rows
FROM market_data.series AS s
JOIN market_data.observations AS o USING (series_id)
WHERE (%s IS NULL OR s.symbol = %s)
GROUP BY s.source_name, s.symbol, s.timeframe
ORDER BY s.source_name, s.symbol, s.timeframe
"""

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute(query, (symbol_filter, symbol_filter))
        rows = cur.fetchall()
```

Source basis: Psycopg parameterized usage plus Phase 1 discovery requirements. [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html] [VERIFIED: .planning/REQUIREMENTS.md]

### Pattern 4: First bridge is CSV materialization, not broad DB refactoring

**What:** Add a command that exports a date-sorted CSV from PostgreSQL so existing forecast/evaluation/training code can consume database-backed data without invasive rewrites. [VERIFIED: codebase grep] [ASSUMED]  
**When to use:** Use this in Phase 1 because `src/run_forecast.py`, `src/evaluate_forecast.py`, and the training path are already file-driven. [VERIFIED: codebase grep]

**Example:**

```python
SELECT open_time_utc AS Date, close_price AS Close
FROM market_data.observations
WHERE series_id = %s
  AND open_time_utc >= %s
  AND open_time_utc < %s
ORDER BY open_time_utc
```

This keeps Phase 1 compatible with current consumers while deferring direct PostgreSQL readers to later phases. [VERIFIED: codebase grep] [ASSUMED]

### Anti-Patterns to Avoid

- **One-table-only storage keyed by ingestion run:** This makes reruns create “new datasets” instead of updating one logical series, which fights `ING-02`. [ASSUMED]
- **Relying on `/docker-entrypoint-initdb.d/` for every future schema change:** Docker docs are explicit that these scripts only run when the data directory is empty. [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] [CITED: https://hub.docker.com/_/postgres]
- **Keeping timestamps only as local time or only as text:** PostgreSQL has native `timestamp with time zone`, and Phase 1 integrity checks need canonical UTC ordering. [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md]
- **Refactoring the entire model stack to direct database reads in Phase 1:** The training and forecast code are currently file-based, and broad DB rewrites would expand scope before the data layer itself is proven. [VERIFIED: codebase grep] [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rerun-safe deduplication | Custom Python “seen timestamp” logic | Primary key on `(series_id, open_time_utc)` plus `INSERT ... ON CONFLICT` | PostgreSQL already gives atomic upsert semantics. [CITED: https://www.postgresql.org/docs/18/sql-insert.html] |
| Bulk row loading | Giant string-built `INSERT` statements | `psycopg` batch execution now, `Cursor.copy()` if ingest volume becomes the bottleneck | Psycopg 3 supports both normal batch execution and COPY protocol. [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html] [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] |
| Manual DBA setup instructions | README steps that tell the user to paste SQL into `psql` by hand | Checked-in `compose.yaml`, init SQL, and a schema bootstrap command | The phase explicitly requires one documented repo-native path and no ad hoc SQL edits. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] |
| Discovery by tribal knowledge | “Inspect the DB yourself” workflow | Scripted discovery and validation CLIs with filtering/sorting | The user explicitly chose script-driven discovery and integrity checks. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] |

**Key insight:** PostgreSQL already solves identity, time-zone-aware storage, upsert, and high-volume load mechanics. Phase 1 should spend engineering effort on schema boundaries and command UX, not on replacing proven database primitives with custom Python logic. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [CITED: https://www.postgresql.org/docs/18/sql-insert.html] [CITED: https://www.postgresql.org/docs/18/sql-copy.html]

## Common Pitfalls

### Pitfall 1: Docker init scripts silently stop running after first boot

**What goes wrong:** Teams add `001_schema.sql`, change it later, rerun `docker compose up`, and assume the live database picked up the edit. [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/]  
**Why it happens:** Docker only runs `/docker-entrypoint-initdb.d` scripts when the data directory is empty. [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] [CITED: https://hub.docker.com/_/postgres]  
**How to avoid:** Use init SQL for first bootstrap only, and plan an explicit schema-apply command for later changes even in Phase 1. [ASSUMED]  
**Warning signs:** You changed SQL, restarted the container, and nothing in the schema moved. [ASSUMED]

### Pitfall 2: Wrong PostgreSQL 18 volume mount target

**What goes wrong:** Data persistence behaves differently than older blog posts suggest because PostgreSQL 18 changed the image’s `PGDATA` and `VOLUME` expectations. [CITED: https://hub.docker.com/_/postgres]  
**Why it happens:** Many older examples mount `/var/lib/postgresql/data`; Docker Hub now documents `/var/lib/postgresql` for 18+. [CITED: https://hub.docker.com/_/postgres]  
**How to avoid:** Follow the PostgreSQL 18 image documentation, not pre-18 snippets copied from older tutorials. [CITED: https://hub.docker.com/_/postgres]  
**Warning signs:** Container recreations lose data or create anonymous volumes unexpectedly. [CITED: https://hub.docker.com/_/postgres]

### Pitfall 3: Naive timestamp handling breaks gap detection and sorting

**What goes wrong:** Missing-minute checks flag false gaps or false duplicates because timestamps were stored as local time or inconsistent text. [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [ASSUMED]  
**Why it happens:** Binance Klines use UTC semantics and identify candles by open time, while local display time and ingestion time are different concepts. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints]  
**How to avoid:** Persist canonical UTC candle times in `timestamptz` and treat ingestion timestamps separately. [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html] [ASSUMED]  
**Warning signs:** Discovery reports sort correctly by text but fail when exported or when daylight-saving boundaries appear. [ASSUMED]

### Pitfall 4: Binance backfill ignores rate limits and retry headers

**What goes wrong:** A one-year backfill trips HTTP 429 or IP bans because pagination does not inspect headers or back off on rate limits. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits]  
**Why it happens:** The Klines endpoint has request weight, and Binance documents 429 plus `Retry-After` behavior. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints] [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits]  
**How to avoid:** Make the ingestion command respect `Retry-After`, expose progress, and checkpoint run metadata even for failed runs. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits] [ASSUMED]  
**Warning signs:** Intermittent partial loads, large coverage gaps, or repeated 429/418 responses. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits]

### Pitfall 5: Scope creep into a PostgreSQL-native training refactor

**What goes wrong:** Phase 1 starts as data setup and becomes a rewrite of `src/main.py`, `src/train.py`, and `src/crypto_minute_backtest.py`. [VERIFIED: codebase grep]  
**Why it happens:** The repo has several file-based consumers, so it is tempting to “finish the job” immediately after the database exists. [VERIFIED: codebase grep] [ASSUMED]  
**How to avoid:** Keep the Phase 1 bridge at materialized CSV export or a single low-risk reader path. [ASSUMED]  
**Warning signs:** Planner tasks start discussing JAX/PAX data loaders or a complete replacement of current CSV flows. [VERIFIED: codebase grep] [ASSUMED]

## Code Examples

Verified patterns from official sources:

### Basic `psycopg` connection and parameterized query

```python
# Source basis: https://www.psycopg.org/psycopg3/docs/basic/usage.html
import psycopg

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_name, symbol, timeframe FROM market_data.series WHERE symbol = %s",
            ("BTCUSDT",),
        )
        rows = cur.fetchall()
```

This follows Psycopg’s documented connection/cursor pattern and keeps SQL injection defenses in the adapter, not in string concatenation. [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html]

### Client-side `COPY` for high-volume imports

```python
# Source basis: https://www.psycopg.org/psycopg3/docs/basic/copy.html
with conn.cursor() as cur:
    with cur.copy(
        "COPY market_data.stage_observations (open_time_utc, close_price) FROM STDIN"
    ) as copy:
        for record in records:
            copy.write_row(record)
```

Use this if the Phase 1 Binance backfill proves too slow with batched upserts alone. [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] The choice between direct upsert and staging-plus-COPY is still a planning decision. [ASSUMED]

### PostgreSQL-native upsert for rerunnable ingestion

```sql
-- Source basis: https://www.postgresql.org/docs/18/sql-insert.html
INSERT INTO market_data.observations (series_id, open_time_utc, close_price, ingestion_run_id)
VALUES ($1, $2, $3, $4)
ON CONFLICT (series_id, open_time_utc) DO UPDATE
SET close_price = EXCLUDED.close_price,
    ingestion_run_id = EXCLUDED.ingestion_run_id;
```

This is the core primitive that satisfies `ING-02` without duplicate rows. [CITED: https://www.postgresql.org/docs/18/sql-insert.html]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `SERIAL` surrogate keys [ASSUMED] | `GENERATED ... AS IDENTITY` for new PostgreSQL tables [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] | Current PostgreSQL 18 docs [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] | New schema should use identity columns instead of older `SERIAL` habits. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] |
| File/server-path-oriented bulk copy habits [ASSUMED] | Client-side `STDIN`/`STDOUT` COPY via psycopg `Cursor.copy()` [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] [CITED: https://www.postgresql.org/docs/18/sql-copy.html] | Psycopg 3 current docs [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] | Phase 1 can bulk load without requiring database-superuser filesystem access. [CITED: https://www.postgresql.org/docs/18/sql-copy.html] |
| Single-file SQLite experiment store in `src/crypto_minute_backtest.py` [VERIFIED: codebase grep] | Dedicated PostgreSQL dataset layer with discovery and provenance [ASSUMED] | Repo roadmap updated 2026-04-13 [VERIFIED: .planning/ROADMAP.md] | Supports multiple assets, date-range queries, and script-driven discovery instead of one-off backtest files. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED] |

**Deprecated/outdated:**

- Treating the existing SQLite backtest file as the long-term data layer is outdated for this roadmap because Phase 1 explicitly shifts the project to PostgreSQL-backed dataset management. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: codebase grep]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 1 should use direct `psycopg` plus checked-in SQL bootstrap instead of introducing SQLAlchemy/Alembic immediately. | Standard Stack | Low to medium; planner might choose a heavier stack than needed. |
| A2 | The safest first downstream bridge is PostgreSQL-to-CSV materialization instead of direct PostgreSQL readers in every existing model/backtest entrypoint. | Summary; Architecture Patterns | Medium; if the user expects direct DB readers immediately, plans may under-scope integration work. |
| A3 | `double precision` is an acceptable first storage type for close prices because current consumers already convert to floats. | Architecture Patterns | Medium; if exact decimal fidelity becomes a hard requirement, schema types and export code should change before implementation. |
| A4 | A separate logical `series` table plus `ingestion_runs` table is the right provenance boundary for this repo. | Architecture Patterns | Low; alternative naming/normalization is possible without changing the broader plan. |

## Open Questions (RESOLVED)

1. **Should Phase 1’s bridge stop at CSV materialization, or must one existing runtime command read PostgreSQL directly?**  
What we know: The context allows a PostgreSQL-to-CSV/materialized dataset step, and the current consumers are file-based. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [VERIFIED: codebase grep]  
What's unclear: Whether the user wants a direct PostgreSQL reader inside `src/crypto_minute_backtest.py` or `src/main.py` already in this phase. [ASSUMED]  
Recommendation: Plan the CSV materialization path as the baseline and leave one explicit “upgrade to direct reader” decision point during discuss/planning if the user pushes for it. [ASSUMED]

2. **Should close prices be stored as `double precision` or `numeric(...)`?**  
What we know: PostgreSQL supports both, and the repo’s current modeling code uses Python/numpy floating-point arrays. [VERIFIED: codebase grep] [ASSUMED]  
What's unclear: Whether the user values exact decimal preservation over simpler/faster float export. [ASSUMED]  
Recommendation: Raise this explicitly in planning; default to `double precision` only if no exact-decimal requirement is stated. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All Phase 1 scripts | ✓ [VERIFIED: local env] | 3.10.11 [VERIFIED: local env] | — |
| `pip` | Installing `psycopg` / `pytest` | ✓ [VERIFIED: local env] | 23.0.1 [VERIFIED: local env] | — |
| Docker CLI | Locked PostgreSQL setup path | ✓ [VERIFIED: local env] | 29.2.1 [VERIFIED: local env] | — |
| Docker Compose CLI | `compose.yaml` workflow | ✓ [VERIFIED: local env] | v5.1.0 [VERIFIED: local env] | — |
| Docker daemon | Actually starting PostgreSQL container | ✗ [VERIFIED: local env] | — | None while `D-01` stays locked to Docker. [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] |
| Host `psql` | Manual inspection convenience | ✗ [VERIFIED: local env] | — | Use `docker compose exec db psql ...` once the daemon is running. [CITED: https://hub.docker.com/_/postgres] |
| `psycopg` package | Python DB access | ✗ in host Python and `.venv` [VERIFIED: local env] | — | None; must install. [CITED: https://pypi.org/project/psycopg/] |
| `pytest` package | Automated validation | ✗ in host Python and `.venv` [VERIFIED: local env] | — | None; must install. [CITED: https://pypi.org/project/pytest/] |
| `pandas` in `.venv` | Discovery/export commands | ✓ in `.venv` only [VERIFIED: local env] | repo environment only [VERIFIED: local env] | Could use standard-library CSV temporarily, but reuse `pandas` is cleaner because it is already a repo dependency. [VERIFIED: requirements.inference.txt] [ASSUMED] |

**Missing dependencies with no fallback:**

- Docker daemon is not running in the current environment, so the locked Docker-based PostgreSQL setup path is execution-blocked until Docker Engine is available. [VERIFIED: local env]
- `psycopg` is not installed in the inspected Python environments. [VERIFIED: local env]

**Missing dependencies with fallback:**

- Host `psql` is missing, but containerized `psql` is an acceptable operator path once Docker is running. [VERIFIED: local env] [CITED: https://hub.docker.com/_/postgres]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest 9.0.3` recommended [CITED: https://pypi.org/project/pytest/] |
| Config file | none detected; create `pytest.ini` only if fixture discovery needs it [VERIFIED: codebase grep] [ASSUMED] |
| Quick run command | `python -m pytest -q tests/test_phase1_postgres.py` [ASSUMED] |
| Full suite command | `python -m pytest -q` [ASSUMED] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DB-01 | Compose-backed PostgreSQL can be reached from project code | integration | `python -m pytest -q tests/test_db_connection.py` | ❌ Wave 0 |
| DB-02 | Schema bootstrap creates tables/indexes without manual SQL | integration | `python -m pytest -q tests/test_schema_bootstrap.py` | ❌ Wave 0 |
| DB-03 | Data can be queried by symbol/source/timeframe/date range | integration | `python -m pytest -q tests/test_discovery_queries.py` | ❌ Wave 0 |
| ING-01 | Binance import command loads target rows | integration | `python -m pytest -q tests/test_binance_ingest.py` | ❌ Wave 0 |
| ING-02 | Re-running ingestion is idempotent | integration | `python -m pytest -q tests/test_binance_ingest.py::test_rerun_idempotent` | ❌ Wave 0 |
| ING-03 | Provenance and coverage metadata are recorded | integration | `python -m pytest -q tests/test_provenance.py` | ❌ Wave 0 |
| DISC-01 | Dataset inventory reports available series and coverage | integration | `python -m pytest -q tests/test_discovery_cli.py::test_inventory_report` | ❌ Wave 0 |
| DISC-02 | Discovery command filters and sorts correctly | integration | `python -m pytest -q tests/test_discovery_cli.py::test_filters_and_sorting` | ❌ Wave 0 |
| DISC-03 | Docs and command help describe schema/workflow | smoke | `python -m pytest -q tests/test_docs_contract.py` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest -q tests/test_db_connection.py` or the smallest touched test file. [ASSUMED]
- **Per wave merge:** `python -m pytest -q` once the Phase 1 suite exists. [ASSUMED]
- **Phase gate:** Full Phase 1 pytest suite green before `/gsd-verify-work`. [ASSUMED]

### Wave 0 Gaps

- [ ] Create a `tests/` root; none exists today. [VERIFIED: codebase grep]
- [ ] Install `pytest`. [VERIFIED: local env] [CITED: https://pypi.org/project/pytest/]
- [ ] Add reusable fixtures for temporary PostgreSQL schema setup and teardown. [ASSUMED]
- [ ] Add a fixture or stub path for Binance responses so ingestion tests are deterministic and do not depend on live API calls. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits] [ASSUMED]
- [ ] Add one smoke test proving CSV materialization is sorted and directly consumable by current CSV-driven scripts. [VERIFIED: codebase grep] [ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes [ASSUMED] | Use PostgreSQL user/password auth with Docker image variables; do not rely on `trust` for host/container connections. [CITED: https://hub.docker.com/_/postgres] |
| V3 Session Management | no [VERIFIED: codebase grep] | No web sessions exist in this CLI-first repo today. [VERIFIED: codebase grep] |
| V4 Access Control | yes [ASSUMED] | Prefer an app-specific DB user over broad superuser use after bootstrap. [ASSUMED] |
| V5 Input Validation | yes [VERIFIED: codebase grep] | Validate symbol, timeframe, date range, and row completeness in the Python CLI before DB writes. [VERIFIED: codebase grep] [ASSUMED] |
| V6 Cryptography | yes, but only for standard mechanisms [ASSUMED] | Use PostgreSQL/Docker standard auth and secrets handling; do not invent custom crypto or credential formats. [CITED: https://hub.docker.com/_/postgres] |

### Known Threat Patterns for PostgreSQL + Python CLI ingestion

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via discovery filters or import parameters | Tampering | Parameterized queries through `psycopg`, never string-build user filters into SQL. [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html] |
| Credential leakage through committed Compose files or docs | Information Disclosure | Keep real passwords out of git and prefer Docker secret/file-based injection for sensitive deployments. [CITED: https://hub.docker.com/_/postgres] [ASSUMED] |
| Silent duplicate or partial ingest | Tampering | Unique observation key, explicit ingestion-run metadata, and validation scripts for gaps/duplicates. [CITED: https://www.postgresql.org/docs/18/sql-insert.html] [VERIFIED: .planning/phases/01-set-up-postgresql-database-download-and-discover-all-data-ad/01-CONTEXT.md] [ASSUMED] |
| API-limit-triggered partial backfills | Denial of Service | Respect 429 and `Retry-After`, and surface run status to the user. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits] |
| Unsafe shelling from `COPY PROGRAM` or server-file COPY | Elevation of Privilege | Use client-side `STDIN` COPY from Python instead of server-side file/program COPY for untrusted inputs. [CITED: https://www.postgresql.org/docs/18/sql-copy.html] [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html] |

## Sources

### Primary (HIGH confidence)

- PostgreSQL 18 docs:
  - `ddl-identity-columns` for `GENERATED ... AS IDENTITY` and current-version status. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html]
  - `datatype-datetime` for `timestamptz`. [CITED: https://www.postgresql.org/docs/18/datatype-datetime.html]
  - `sql-insert` for `ON CONFLICT` behavior and unique-index inference. [CITED: https://www.postgresql.org/docs/18/sql-insert.html]
  - `sql-copy` for COPY behavior and client/server boundaries. [CITED: https://www.postgresql.org/docs/18/sql-copy.html]
- Docker:
  - Official `postgres` image docs for tags, Compose usage, auth variables, PGDATA changes, and init-script behavior. [CITED: https://hub.docker.com/_/postgres]
  - Docker PostgreSQL guide for first-run init scripts and mounted SQL examples. [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/]
- Psycopg:
  - PyPI package page for current version and install extras. [CITED: https://pypi.org/project/psycopg/]
  - Psycopg usage docs for connection/cursor/query patterns. [CITED: https://www.psycopg.org/psycopg3/docs/basic/usage.html]
  - Psycopg COPY docs for `Cursor.copy()`. [CITED: https://www.psycopg.org/psycopg3/docs/basic/copy.html]
- Binance:
  - Spot Market Data docs for Klines endpoint semantics, limits, and open-time identity. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints]
  - Spot REST Limits docs for rate-limit and backoff behavior. [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits]
- Local repo evidence:
  - `.planning` phase/context/requirements docs and codebase grep across `src/`, `scripts/`, and `README.md`. [VERIFIED: codebase grep]

### Secondary (MEDIUM confidence)

- `pytest` PyPI page for recommended current test framework version compatible with Python 3.10. [CITED: https://pypi.org/project/pytest/]
- SQLAlchemy and Alembic PyPI pages for alternative-stack comparison only. [CITED: https://pypi.org/project/SQLAlchemy/] [CITED: https://pypi.org/project/alembic/]

### Tertiary (LOW confidence)

- None. All external factual claims above were tied to official docs, official package pages, or direct codebase inspection. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH because the core recommendations are grounded in official PostgreSQL, Docker, Psycopg, and Binance docs plus local environment checks. [CITED: https://www.postgresql.org/docs/18/ddl-identity-columns.html] [CITED: https://hub.docker.com/_/postgres] [CITED: https://pypi.org/project/psycopg/] [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints] [VERIFIED: local env]
- Architecture: MEDIUM because the repo integration shape and first bridge strategy are informed by verified codebase structure but still involve design judgment. [VERIFIED: codebase grep] [ASSUMED]
- Pitfalls: HIGH because the most important pitfalls come directly from official Docker/PostgreSQL/Binance docs and verified current repo constraints. [CITED: https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/] [CITED: https://hub.docker.com/_/postgres] [CITED: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits] [VERIFIED: codebase grep]

**Research date:** 2026-04-13 [VERIFIED: .planning/STATE.md]  
**Valid until:** 2026-05-13 for stack/version checks unless the phase slips and package/container versions need re-verification. [ASSUMED]
