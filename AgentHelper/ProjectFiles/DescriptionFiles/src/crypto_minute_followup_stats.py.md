# `src/crypto_minute_followup_stats.py`

This module is a model-free PostgreSQL analysis CLI for Binance 1-minute close
prices. It loads the same kind of UTC day window used by the crypto backtest,
but instead of calling TimesFM it treats one reference candle as the baseline,
compares the next N candles against that baseline, and writes a plain-text
report with per-step direction counts and deviation averages.

Key responsibilities:

- parse PostgreSQL connection and UTC day-range CLI arguments for minute-candle analysis
- load canonical `binance` / `1m` close-price candles from `market_data.observations`
- include a one-candle lookback so the first requested candle can still be measured against the immediately preceding close
- slide rolling windows across the loaded data without any model dependency
- classify each future candle as above, below, or matching the reference candle close
- compute per-step close-difference averages and normalized deviation percentages using the shared backtest metric formula
- write a backtest-style text report under `outputs/backtests/` by default and print a short execution summary

Important interactions:

- imports `normalized_deviation_pct()` from `src/backtest_metrics.py`
- imports PostgreSQL settings and connection helpers from `src/postgres_dataset.py`
- reads from the Phase 1 canonical market-data tables and does not write new database rows
- is exercised by `tests/test_crypto_minute_followup_stats.py`

Category: model-free data analysis entrypoint.
