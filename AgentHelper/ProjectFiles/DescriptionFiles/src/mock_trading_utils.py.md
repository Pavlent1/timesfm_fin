# `src/mock_trading_utils.py`

This helper module loads and normalizes market datasets for the mock trading workflow. It contains market-specific branches for `topix500`, `sp500`, `forex`, `crypto_hourly`, and `crypto_daily`, with separate helpers for loading raw prices versus return-oriented data.

Important details:

- depends on a `data_paths` module outside the approved scope to resolve default dataset locations
- applies asset-specific filtering, pivoting, forward-filling, and date trimming
- is used by both `src/mock_trading.py` and `src/mock_trading.ipynb`

Category: experiment data-loading utility.
