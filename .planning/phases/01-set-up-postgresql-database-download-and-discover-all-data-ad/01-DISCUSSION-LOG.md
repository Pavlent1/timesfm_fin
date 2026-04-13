# Phase 1: Set up PostgreSQL database, download and discover all data, add sorting and organization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 1-set-up-postgresql-database-download-and-discover-all-data-ad
**Areas discussed:** Phase boundary, PostgreSQL setup path, data model, discovery and integrity

---

## Phase boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Storage only | Only stand up PostgreSQL plus basic ingestion/discovery | |
| Include path | Include a practical path into later training/backtest use | x |
| Let the agent decide | Planner can narrow the phase later | |

**User's choice:** Include path.
**Notes:** Follow-up on the exact integration shape was left to the agent: "Do as better, I dont know, if it works it will be fine."

---

## PostgreSQL setup path

| Option | Description | Selected |
|--------|-------------|----------|
| External instance | Assume a pre-existing PostgreSQL server | |
| Local Docker PostgreSQL with YAML | Repo-owned local setup and orchestration | x |
| Let the agent decide | Pick the simplest path during planning | |

**User's choice:** Local Docker-based PostgreSQL with YAML.
**Notes:** The user explicitly wanted the setup owned by the repo rather than an external manual dependency.

---

## Data model

| Option | Description | Selected |
|--------|-------------|----------|
| BTC-only narrow schema | Optimize only for the first Bitcoin ingestion case | |
| Multi-symbol support now | Design for multiple assets immediately | x |
| Generalize later | Keep v1 narrow and refactor later | |

**User's choice:** Multi-symbol support now.
**Notes:** The user still wants Phase 1 storage kept narrow in data shape: for now, 1-minute candles are enough, and the first concrete script should target Bitcoin.

---

## Discovery and integrity

| Option | Description | Selected |
|--------|-------------|----------|
| SQL/docs only | Users inspect data manually in PostgreSQL | |
| Discovery scripts only | Scripted summaries without full integrity audits | |
| Discovery plus integrity scripts | Scripted summaries and validation tooling | x |

**User's choice:** Discovery plus integrity scripts.
**Notes:** Required checks include duplicates, missing minute gaps, ordering issues, nulls, out-of-range timestamps, and coverage summaries. The user emphasized that cleaner data should improve downstream results.

---

## the agent's Discretion

- Choose the simplest reliable first bridge from PostgreSQL-backed data into the existing training/backtest workflow shape.

## Deferred Ideas

- Recurring scheduled PostgreSQL refresh jobs
- Real-time streaming ingestion
- Broader market-data shapes beyond the initial 1-minute close-price focus
