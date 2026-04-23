# `src/backtest_metrics.py`

This module is the Phase 2 source of truth for per-step backtest metric semantics. It keeps the normalized deviation formula, overshoot-versus-undershoot classification, signed percent deviation, side-of-last-input direction correctness, and the locked conditional move-threshold defaults in one pure helper layer that later runtime and PostgreSQL code can reuse without reinterpreting the rules.

Key responsibilities:

- compute normalized deviation percent from predicted and actual close values
- classify overshoot, undershoot, and exact matches relative to `last_input_close`
- derive signed deviation percent where overshoot is positive and undershoot is negative
- classify whether predicted and actual closes finish above, below, or exactly on the last input close
- expose a reusable 1-or-0 direction-correct flag for per-step aggregation
- compute absolute percent move magnitude from `last_input_close` to an arbitrary close
- expose the explicit default conditional move-threshold table for human-facing steps 1 through 5
- package the per-step metric fields needed by later persistence and aggregation code

Important interactions:

- is imported directly by future backtest runtime and PostgreSQL helper modules under `src/`
- is locked by `tests/test_backtest_metrics.py`
- does not depend on CLI parsing, TimesFM, SQLite, or PostgreSQL state

Category: reusable backtest metric helpers.
