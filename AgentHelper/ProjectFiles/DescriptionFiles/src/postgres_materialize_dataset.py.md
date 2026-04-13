# `src/postgres_materialize_dataset.py`

CLI and helpers for exporting PostgreSQL Phase 1 data into the CSV layouts the existing repo already understands.

Key responsibilities:

- parse discovery-style filters plus the output mode and destination path
- load matching observations from PostgreSQL
- export a single-series chronological `Date` / `Close` CSV for forecast and evaluation scripts
- export a numeric aligned training matrix for the existing `src/train.py` preprocessing flow
- write the resulting CSV and print a short operator summary

Important interactions:

- reuses the same source/symbol/timeframe/date filter model as the Phase 1 discovery tools
- bridges the PostgreSQL data layer back into the current CSV-first modeling entrypoints without refactoring them to read PostgreSQL directly

Category: PostgreSQL materialization CLI.
