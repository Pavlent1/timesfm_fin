# Phase 03: User Setup Required

**Generated:** 2026-04-16
**Phase:** 03-train-the-model-on-1-minute-crypto-candles
**Status:** Incomplete

Complete these items before using the Phase 3 source-readiness workflow. The agent automated the code changes; these runtime prerequisites still need operator confirmation.

## Environment Variables

None.

## Account Setup

None.

## Dashboard Configuration

None.

## Local Runtime Prerequisites

- [ ] **Start the local PostgreSQL service**
  - Command: `docker compose up -d postgres`
  - Why: `src/postgres_prepare_training_source.py` verifies readiness against PostgreSQL and reuses the canonical ingest path.

- [ ] **Confirm Binance HTTP access is available from the intended runtime**
  - Why: the manual source-preparation CLI backfills missing coverage through the Binance klines API before re-checking readiness.

## Verification

After completing setup, verify with:

```bash
docker compose ps postgres
python src/postgres_prepare_training_source.py --skip-backfill
```

Expected results:
- The `postgres` container is `running` or `healthy`.
- The source-readiness CLI can connect to PostgreSQL and print readiness findings instead of failing on missing infrastructure.
