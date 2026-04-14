# `src/backtest_metrics.py`

This module is the Phase 2 source of truth for per-step backtest metric semantics. It keeps the normalized deviation formula, overshoot-versus-undershoot classification, and signed percent deviation in one pure helper layer that later runtime and PostgreSQL code can reuse without reinterpreting the rules.

Key responsibilities:

- compute normalized deviation percent from predicted and actual close values
- classify overshoot, undershoot, and exact matches relative to `last_input_close`
- derive signed deviation percent where overshoot is positive and undershoot is negative
- package the per-step metric fields needed by later persistence and aggregation code

Important interactions:

- is imported directly by future backtest runtime and PostgreSQL helper modules under `src/`
- is locked by `tests/test_backtest_metrics.py`
- does not depend on CLI parsing, TimesFM, SQLite, or PostgreSQL state

Category: reusable backtest metric helpers.
