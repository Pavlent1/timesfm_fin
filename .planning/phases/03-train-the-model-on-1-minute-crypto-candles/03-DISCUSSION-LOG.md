# Phase 3: Train the model on 1-minute crypto candles - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `03-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 03-train-the-model-on-1-minute-crypto-candles
**Areas discussed:** dataset scope, training slice policy, holdout policy, data cleaning/preparation, snapshot tracking, retraining workflow

---

## Dataset Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Three supported pairs only | Keep Phase 3 focused on `BTCUSDT`, `ETHUSDT`, and `SOLUSDT` | x |
| Configurable symbol universe | Build the phase for arbitrary crypto pairs from day one | |

**User's choice:** Three supported pairs only for now.
**Notes:** Binance spot `1m` remains the inherited source and timeframe from the existing data foundation.

---

## Training Slice Policy

| Option | Description | Selected |
|--------|-------------|----------|
| One shared calendar month | All symbols use the same month window | |
| One rolling 30-day window | All symbols use one rolling 30-day slice | |
| Fully custom per-symbol range | Each symbol can use its own explicit `start` / `end` dates | x |

**User's choice:** Fully custom per-symbol range.
**Notes:** The first intended training round is still one month from each crypto, but the workflow must support custom per-symbol slices rather than force one global window.

---

## Holdout Policy

| Option | Description | Selected |
|--------|-------------|----------|
| No reserved holdout | Consume all available data for training | |
| Fixed 4-month holdout for all | Reserve the last four months on every pair | |
| Configurable per-symbol holdout | Holdout range is explicit and can differ per symbol | x |

**User's choice:** Configurable per-symbol holdout.
**Notes:** Bitcoin is the concrete default example: 40 months total with the last 4 months preserved for backtests.

---

## Data Cleaning And Preparation

| Option | Description | Selected |
|--------|-------------|----------|
| Strict only | Drop anything not fully clean and aligned | |
| Repair only | Fill or normalize where safe, then proceed | |
| Both modes + report | Produce cleaned output with selectable strict/repair behavior and a quality report | x |

**User's choice:** Both modes plus reporting.
**Notes:** The user explicitly wants research on what the model can and cannot take as input, so the exact preparation contract remains a research item for planning.

---

## Snapshot Tracking

| Option | Description | Selected |
|--------|-------------|----------|
| Checkpoint files only | Save weights with no structured run manifest | |
| Recommended baseline manifest | Save checkpoint, parent checkpoint, symbol/date selections, holdouts, preparer settings, training config, and eval/backtest summary | x |
| Minimal metadata | Save only a short note beside the checkpoint | |

**User's choice:** Recommended baseline manifest.
**Notes:** The goal is future comparison of how each newly added training dataset affects outcomes.

---

## Retraining Workflow

| Option | Description | Selected |
|--------|-------------|----------|
| Manual repeatable CLI | Reusable user-invoked workflow for repeated training runs | x |
| Scheduled runner | Include periodic or unattended retraining in this phase | |

**User's choice:** Manual repeatable CLI only.
**Notes:** Scheduling is intentionally deferred.

---

## the agent's Discretion

- Exact CLI flag design for per-symbol ranges and presets.
- Exact repair thresholds and cleaner report format.
- Exact storage shape for snapshot manifests and lineage metadata.

## Deferred Ideas

- Scheduled retraining.
- Expansion beyond BTC, ETH, and SOL in Phase 3.
