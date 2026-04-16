# `src/crypto_minute_backtest.py`

This is the PostgreSQL-backed crypto backtest runtime entrypoint. It reads one
or more UTC days of Binance minute candles from the shared Phase 1 PostgreSQL
dataset for historical backtests, includes a configurable context lookback
before the requested evaluation span so a "one day" run can still forecast from
the first requested candle onward, persists live-mode Binance fetches back into
PostgreSQL, runs rolling TimesFM forecasts, and stores run, window, and
per-step prediction facts through the shared Phase 2 backtest helpers without
computing or printing the older legacy summary metrics.

Key responsibilities:

- parse backtest and live-mode CLI arguments, including multi-day historical spans
- build PostgreSQL connection settings from CLI flags and environment defaults
- read canonical source candles from `market_data.observations` for backtests,
  including the pre-range context window required for the first evaluated window
- fetch recent Binance klines for live mode and persist them into PostgreSQL ingestion tables
- batch forecast windows through TimesFM for faster rolling evaluation
- store `market_data.backtest_runs`, `market_data.backtest_windows`, and `market_data.backtest_prediction_steps` rows through the shared helper layer, using the actual loaded candle span for persisted run coverage
- write a plain-text backtest report under `outputs/backtests/` by default so operators can inspect run results and per-step stats, including per-output-candle direction-guess accuracy, without querying PostgreSQL manually
- print run summaries that distinguish requested evaluation candles from the loaded lookback context, point operators to the per-step PostgreSQL view, and show the saved report path, then optionally export live forecasts to CSV

Important interactions:

- imports `DEFAULT_REPO_ID` and `build_model` from `src/run_forecast.py`
- imports `build_step_metrics()` from `src/backtest_metrics.py`
- imports `create_backtest_run()`, `create_backtest_window()`, and `insert_backtest_steps()` from `src/postgres_backtest.py`
- imports shared PostgreSQL connection and ingestion helpers from `src/postgres_dataset.py`
- imports `fetch_binance_klines()` from `src/binance_market_data.py`
- is launched directly or through `scripts/run_crypto_backtest.ps1`

Category: data ingestion and backtesting entrypoint.
