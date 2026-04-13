# `src/crypto_minute_backtest.py`

This is the most feature-rich runtime script in the repo. It fetches Binance 1-minute candles, stores them in SQLite, runs either a rolling TimesFM backtest or a single live forecast, computes trading-style metrics, and persists both run summaries and per-window predictions.

Key responsibilities:

- parse backtest and live-mode CLI arguments
- fetch paginated Binance kline data over HTTP through the shared `src/binance_market_data.py` helper
- create and maintain the SQLite schema in `candles`, `backtest_runs`, and `backtest_predictions`
- batch forecast windows through TimesFM for faster rolling evaluation
- derive error metrics, directional hit rate, and return-based statistics such as annualized volatility and Sharpe ratio
- print run summaries and optionally export live forecasts to CSV

Important interactions:

- imports `directional_accuracy`, `mape`, and `smape` from `src/evaluate_forecast.py`
- imports `DEFAULT_REPO_ID` and `build_model` from `src/run_forecast.py`
- imports `fetch_binance_klines()`, `to_utc_iso()`, and `ONE_MINUTE_MS` from `src/binance_market_data.py`
- is launched directly or through `scripts/run_crypto_backtest.ps1`

Category: data ingestion and backtesting entrypoint.
