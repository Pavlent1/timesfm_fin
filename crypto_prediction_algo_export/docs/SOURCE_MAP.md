# Source Map

This export was derived from the following repo files.

## Primary Logic Sources

- `backend/data/crypto.py`
  - BTC candle feature engineering
  - RSI
  - momentum
  - VWAP
  - SMA crossover
  - volatility

- `backend/core/signals.py`
  - signal mapping
  - convergence rule
  - composite weighting
  - probability transform
  - edge selection
  - confidence heuristic
  - Kelly sizing
  - actionable filter logic

- `backend/config.py`
  - threshold and weight defaults

- `backend/api/main.py`
  - calibration summary logic used by the dashboard API

## What Was Intentionally Left Out

- exchange/API fetchers
- Polymarket event fetching
- FastAPI endpoints
- database persistence
- scheduler
- settlement engine
- frontend

The goal of this export is portability for analysis and backtesting, not a runnable trading service.
