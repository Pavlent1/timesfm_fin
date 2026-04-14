# Phase 2: create-backtest-architecture-qualification-rules-and-statist - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-14
**Phase:** 02-create-backtest-architecture-qualification-rules-and-statist
**Areas discussed:** Canonical database, persistence grain, metric semantics, overshoot/undershoot rules

---

## Canonical database

| Option | Description | Selected |
|--------|-------------|----------|
| PostgreSQL for both source candles and backtest results/statistics | One canonical database for all persistent market and backtest data. | ✓ |
| PostgreSQL for source candles, SQLite for backtest runs/statistics | Keep a split persistence model. | |
| Another split | Use a custom storage boundary. | |

**User's choice:** PostgreSQL for both source candles and backtest results/statistics.
**Notes:** The user wants only one database for everything in the repository.

---

## Persistence grain

| Option | Description | Selected |
|--------|-------------|----------|
| One row per predicted step of every window | Store raw step facts so later queries and new metrics stay easy. | ✓ |
| One row per window plus separate aggregated per-step statistics | Lower row count but less flexible for later analysis. | |
| Another structure | User-defined custom structure. | |

**User's choice:** One row per predicted step of every window.
**Notes:** The user wants optimized querying from the database and wants statistics per output candle position.

---

## Phase naming clarification

| Option | Description | Selected |
|--------|-------------|----------|
| Separate qualification-rules engine | Treat "qualification rules" as a distinct rules subsystem. | |
| Metrics/statistics pipeline only | Treat the phase as backtest structure plus statistics collection. | ✓ |

**User's choice:** Metrics/statistics pipeline only.
**Notes:** The user clarified that "qualification rules" was a misunderstanding and the intended scope is the statistics side of the backtest infrastructure.

---

## Overshoot and undershoot rules

| Option | Description | Selected |
|--------|-------------|----------|
| Judge against the last input candle close | Use the final context candle as the baseline for over/undershoot classification. | ✓ |
| Judge only against actual close without context baseline | Ignore the last input candle in the classification rule. | |

**User's choice:** Judge against the last input candle close.
**Notes:** Confirmed examples:
- With `last_input_close = 100`, actual `105`, prediction `108` is overshoot.
- With `last_input_close = 100`, actual `105`, prediction `102` is undershoot.
- With `last_input_close = 100`, actual `95`, prediction `92` is overshoot downward.
- With `last_input_close = 100`, actual `95`, prediction `98` is undershoot downward.
- Overshoot and undershoot should also be recorded in percent relative to the actual price.

---

## Accuracy metric semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Raw ratio only | Store `predicted_close / actual_close` only. | |
| Normalized deviation only | Store normalized percent deviation from perfect prediction. | ✓ |
| Both | Store both the raw ratio and the normalized deviation. | |

**User's choice:** Normalized deviation only.
**Notes:** The user wants the accuracy statistic to account for both overshoot and undershoot symmetrically by converting the ratio to distance from `1.0`. The intended formula is `abs((predicted_close / actual_close) - 1.0) * 100`, and this same normalized metric should be used for standard deviation calculations.

---

## Overshoot/undershoot signed storage

| Option | Description | Selected |
|--------|-------------|----------|
| Classification label only | Save just `overshoot` or `undershoot`. | |
| Signed deviation only | Save only signed numeric deviation. | |
| Both | Save the label and the signed deviation. | ✓ |

**User's choice:** Both.
**Notes:** The user wants both a categorical classification and a signed numeric measure available for later analysis.

## the agent's Discretion

- Exact PostgreSQL schema names, indexing strategy, and whether per-step aggregates are materialized or derived at query time.
- Exact handling of neutral/no-move cases and perfect matches, provided the stored metrics stay consistent with the formulas above.

## Deferred Ideas

None.
