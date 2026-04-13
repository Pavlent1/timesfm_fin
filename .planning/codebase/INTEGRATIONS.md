# External Integrations

**Analysis Date:** 2026-04-13

## APIs & External Services

**Market Data APIs:**
- Yahoo Finance - Historical price download for ticker-based forecasts and rolling evaluations
  - SDK/Client: `yfinance` loaded inside `src/run_forecast.py`
  - Auth: None configured in the repo; the current implementation calls `yf.download(...)` without credentials
  - Endpoints used: Indirect through the `yfinance` client in `src/run_forecast.py`; reused by `src/evaluate_forecast.py`
- Binance Spot REST API - Public 1-minute candle ingestion for crypto backtests and live minute forecasts
  - SDK/Client: Python standard library `urllib.request` in `src/crypto_minute_backtest.py`
  - Auth: None configured in the repo; requests are made against the public `https://api.binance.com/api/v3/klines` endpoint
  - Endpoints used: `api/v3/klines` in `src/crypto_minute_backtest.py`

**Model Registry / Checkpoint Sources:**
- Hugging Face model repositories - TimesFM checkpoints are resolved by repo id at runtime
  - Integration method: `timesfm.TimesFmCheckpoint(huggingface_repo_id=...)`
  - Auth: No token or secret wiring is present in the repo; access is implicit through the `timesfm` package
  - Repos used: `pfnet/timesfm-1.0-200m-fin` by default in `src/run_forecast.py`; `google/timesfm-1.0-200m` by default in `src/main.py`

## Data Storage

**Databases:**
- SQLite - Local persistence for crypto candles, backtest runs, and per-window predictions
  - Connection: CLI path via `--db-path` in `src/crypto_minute_backtest.py`
  - Client: Python standard library `sqlite3`
  - Schema management: Created in code by `ensure_schema(...)` in `src/crypto_minute_backtest.py`

**File Storage:**
- Local filesystem only
  - Forecast CSV outputs are written by `src/run_forecast.py` and `src/evaluate_forecast.py`
  - Training logs and checkpoints are written under the user-provided `--workdir` in `src/main.py`, `src/train.py`, `src/evaluation.py`, and `src/train_flax.py`
  - Mock trading outputs are written under `--workdir` in `src/mock_trading.py`
  - Training and inference can also read local CSV inputs via `--csv` and local datasets via `--dataset_path`

**Caching:**
- None detected - The inspected code reads from APIs, local files, or SQLite directly without a cache service

## Authentication & Identity

**Auth Provider:**
- None - The repository does not implement user authentication, session management, or identity provider integration

**OAuth Integrations:**
- Not applicable

## Monitoring & Observability

**Error Tracking:**
- None detected - No Sentry, Rollbar, or equivalent SDK is imported in the inspected roots

**Logs:**
- Local process logging and metric files
  - `absl.logging` is used in `src/main.py`
  - Python `logging` is used in `src/train.py`, `src/evaluation.py`, and `src/train_flax.py`
  - `clu.metric_writers` is used in `src/train.py` and `src/evaluation.py`
  - TensorBoard-compatible summaries are written from `src/train_flax.py`

## CI/CD & Deployment

**Hosting:**
- Docker or direct local execution
  - Deployment: `Dockerfile` packages the inference path with `src/run_forecast.py` as the container entrypoint
  - Environment vars: No secret-bearing environment variables are required by the inspected code paths

**CI Pipeline:**
- Not detected in the inspected roots and root runtime files

## Environment Configuration

**Development:**
- Required env vars: None detected for external service auth
- Secrets location: Not applicable; the inspected code does not reference secret-bearing env vars or credential files
- Mock/stub services: Not implemented; development uses live public services or local files

**Staging:**
- Not applicable - No separate staging environment or staging-only service configuration is defined in the inspected files

**Production:**
- Secrets management: Not applicable in the current repo state
- Failover/redundancy: Not implemented in code; operational resilience depends on the availability of Yahoo Finance, Binance, Hugging Face checkpoint access, local filesystem paths, and local SQLite storage

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- Yahoo Finance pulls triggered by `--ticker` or `--tickers` in `src/run_forecast.py` and `src/evaluate_forecast.py`
- Binance candle pulls triggered by `src/crypto_minute_backtest.py`
- Hugging Face checkpoint fetches triggered when `src/run_forecast.py` or `src/main.py` constructs a `TimesFmCheckpoint` from a repo id

---

*Integration audit: 2026-04-13*
