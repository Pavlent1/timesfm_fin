# `src/postgres_backtest.py`

Shared PostgreSQL persistence helpers for Phase 2 backtest artifacts.

Key responsibilities:

- insert canonical backtest run rows into `market_data.backtest_runs`
- insert per-window rows into `market_data.backtest_windows`
- insert batched per-step rows into `market_data.backtest_prediction_steps`
- query `market_data.backtest_step_stats_vw` for one run in step order

Important interactions:

- assumes `src/postgres_dataset.py` bootstrap has already applied the checked-in Phase 2 schema SQL
- uses direct parameterized `psycopg` SQL with `%s` placeholders and `RETURNING` for generated IDs
- stays independent from CLI parsing, Binance fetching, and metric-formula calculation so runtime code can pass already-computed values in

Category: shared PostgreSQL backtest helper layer.
