# `src/evaluate_forecast.py`

This file provides a rolling backtest CLI for the finance-tuned TimesFM model on either one CSV series or multiple Yahoo Finance tickers. It shares data-loading and model-construction helpers from `src/run_forecast.py`, then evaluates repeated forecast windows over the tail of each series and computes aggregate forecast error and directional metrics.

Key responsibilities:

- parse evaluation-specific CLI options such as `test_points` and `stride`
- compute `mae`, `rmse`, `mape`, `smape`, and two directional-accuracy variants
- evaluate one or more series by repeatedly slicing context and target windows
- format and optionally persist a summary table

This file is analysis-oriented rather than training-oriented. `src/crypto_minute_backtest.py` imports its metric helpers for minute-level crypto experiments.

Category: evaluation entrypoint.
