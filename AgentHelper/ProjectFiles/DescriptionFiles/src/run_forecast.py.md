# `src/run_forecast.py`

This file is the main inference CLI for running the finance-tuned TimesFM checkpoint on either Yahoo Finance data or a local CSV. It parses command-line options, loads a single price series, builds a TimesFM model from the requested backend and checkpoint repo, runs one forecast, prints the result, and optionally writes the forecast table to CSV.

Key responsibilities:

- load one series from Yahoo Finance or CSV with basic validation
- infer a future datetime index when the input series has a regular `DatetimeIndex`
- construct the TimesFM JAX checkpoint and hyperparameter objects
- run a single forecast window from the latest `context_len` observations

Important interactions:

- reused by `src/evaluate_forecast.py` for shared data-loading and model-building helpers
- reused by `src/crypto_minute_backtest.py` for `DEFAULT_REPO_ID` and `build_model`
- depends on `yfinance`, `pandas`, `numpy`, and `timesfm`

Category: inference entrypoint.
