# Architecture

**Analysis Date:** 2026-04-13

## Pattern Overview

**Overall:** Flat script-oriented ML repository with two main execution paths: a legacy JAX/Pax fine-tuning pipeline and a newer inference/backtest CLI toolset.

**Key Characteristics:**
- Source lives in a flat `src/` module namespace rather than a Python package, so files import each other by filename such as `import train` and `from run_forecast import build_model`.
- Training and evaluation code in `src/main.py`, `src/train.py`, and `src/evaluation.py` is tightly coupled to TimesFM v1, JAX, PaxML, and Praxis.
- Inference and benchmarking code in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py` forms a lighter CLI-oriented path with shared model-construction helpers.
- Operational entry from Windows is delegated to `scripts/*.ps1`, while container execution is defined in `Dockerfile`.

## Layers

**Entry And Orchestration Layer:**
- Purpose: Parse CLI arguments or flags, select execution mode, and hand off to the appropriate pipeline.
- Location: `src/main.py`, `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/mock_trading.py`, `scripts/run_crypto_backtest.ps1`, `scripts/setup_windows.ps1`, `Dockerfile`
- Contains: `argparse` CLIs, `absl.flags` entrypoints, Docker startup configuration, and PowerShell wrappers.
- Depends on: Training, inference, evaluation, and data helper modules in `src/`; root packaging files such as `Dockerfile` and `requirements.inference.txt`.
- Used by: Developers running `python ...`, `docker run ...`, or the PowerShell wrapper scripts.

**Training And Fine-Tuning Layer:**
- Purpose: Convert price-history CSVs into training/evaluation batches, wrap the upstream TimesFM decoder for finance fine-tuning, and run replicated training plus checkpointing.
- Location: `src/train.py`, `src/evaluation.py`, `configs/fine_tuning.py`, `src/utils.py`
- Contains: Dataset preprocessing, batch reshaping, learner construction, custom model subclassing, `jax.pmap` training/evaluation steps, TensorBoard logging, and checkpoint save/restore flows.
- Depends on: `timesfm`, `jax`, `tensorflow`, `paxml`, `praxis`, and the config module `configs/fine_tuning.py`.
- Used by: `src/main.py` for normal training and checkpoint evaluation runs.

**Inference And Benchmarking Layer:**
- Purpose: Build TimesFM checkpoints for prediction, load one or more time series, run forecasts, and compute rolling evaluation metrics.
- Location: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`
- Contains: Yahoo Finance loaders, CSV loaders, future-index inference, TimesFM model factory logic, rolling window evaluation, Binance fetch/persist logic, and SQLite-backed result storage.
- Depends on: `timesfm`, `numpy`, `pandas`, public data APIs, and helper reuse across `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Used by: Direct CLI runs, `Dockerfile` container entry, and `scripts/run_crypto_backtest.ps1`.

**Experimental And Legacy Analysis Layer:**
- Purpose: Keep older or ad hoc workflows that are adjacent to, but not central to, the current forecast/backtest path.
- Location: `src/train_flax.py`, `src/mock_trading.py`, `src/mock_trading_utils.py`, `src/mock_trading.ipynb`
- Contains: A deprecated Flax-based training implementation, a mock-trading signal generator, dataset loading helpers, and notebook-based exploration.
- Depends on: Local CSV inputs and, in the case of `src/mock_trading_utils.py`, an external `data_paths.py` module that is ignored by `.gitignore`.
- Used by: Manual experiments rather than the documented Docker or inference path.

## Data Flow

**Fine-Tuning Run:**

1. A user runs `python src/main.py --workdir ... --config configs/fine_tuning.py --dataset_path ...`.
2. `src/main.py` loads the `ml_collections` config, injects `dataset_path`, builds a base `timesfm.TimesFm` checkpoint, and selects training or evaluation via `--do_eval`.
3. `src/train.py` or `src/evaluation.py` calls `preprocess_csv()` to read the dataset, transpose it into series-per-row form, and create TensorFlow datasets.
4. `src/train.py` wraps the upstream decoder with `PatchedDecoderFinetuneFinance`, builds a Pax learner via `build_learner()`, and initializes replicated JAX model state from the upstream checkpoint.
5. The training or evaluation loop uses `jax.pmap` over `train_step()` and `eval_step()`, computes accuracy-style metrics through `src/utils.py`, and logs to TensorBoard plus a file logger under the requested work directory.
6. Training periodically saves checkpoints to `workdir/checkpoints/...`; evaluation restores model state from the provided checkpoint and reports per-horizon metrics.

**Single Forecast Run:**

1. A user runs `python src/run_forecast.py ...` directly or starts the container from `Dockerfile`.
2. `src/run_forecast.py` parses CLI options and loads either one Yahoo Finance series or one local CSV series.
3. The script trims the latest `context_len` values, validates that at least 32 observations remain, and constructs a TimesFM model via `build_model()`.
4. `model.forecast()` runs once on the single context window.
5. The script formats the prediction into a `pandas.DataFrame`, optionally infers future timestamps, writes CSV output when requested, and prints a console summary.

**Rolling Evaluation Run:**

1. A user runs `python src/evaluate_forecast.py --tickers ...` or `--csv ...`.
2. `src/evaluate_forecast.py` reuses `load_series_from_yahoo()`, `load_series_from_csv()`, and `build_model()` from `src/run_forecast.py`.
3. `evaluate_series()` slides a rolling origin across the last part of the series, calls `model.forecast()` per window, and accumulates predictions and actuals.
4. Metrics such as MAE, RMSE, MAPE, SMAPE, and directional accuracy are computed in-process and returned as a summary table.
5. Results are printed and optionally saved as a CSV file.

**Crypto Backtest Or Live Forecast Run:**

1. A user runs `python src/crypto_minute_backtest.py ...` directly or uses `scripts/run_crypto_backtest.ps1`, which builds and launches Docker.
2. `src/crypto_minute_backtest.py` opens a SQLite database, creates schema through `ensure_schema()`, and fetches Binance 1-minute candles with `fetch_binance_klines()`.
3. Historical mode persists the candle set, reloads it into a `pandas.DataFrame`, batches forecast windows, and reuses `build_model()` from `src/run_forecast.py`.
4. `run_backtest()` computes per-window predictions plus summary metrics, then `save_backtest()` writes run-level and window-level records into SQLite tables.
5. Live mode reuses the same model path but only forecasts the latest closed minute window and optionally writes the resulting forecast table to CSV.

**State Management:**
- Execution state is run-local and in-memory; there is no long-lived application service or package-wide state container.
- Persistent artifacts are file-based: training writes logs and checkpoints under the user-supplied `workdir`, single-run inference can emit CSVs, and crypto backtests persist candles plus metrics into a SQLite database under `outputs/` by default.
- Configuration is split between CLI flags in `src/*.py`, one reusable config module at `configs/fine_tuning.py`, and environment/platform setup from `Dockerfile` or `scripts/setup_windows.ps1`.

## Key Abstractions

**TimesFM Model Factory:**
- Purpose: Centralize TimesFM checkpoint and hyperparameter construction for forecasting workflows.
- Examples: `src/run_forecast.py` `build_model()`, `src/main.py` `timesfm.TimesFmCheckpoint(...)`
- Pattern: Direct factory function or direct instantiation around upstream `timesfm` objects.

**Finance Fine-Tune Adapter:**
- Purpose: Override the upstream patched decoder so the loss and prediction path match the repo's finance training assumptions.
- Examples: `src/train.py` `PatchedDecoderFinetuneFinance`
- Pattern: Subclass-and-override of `timesfm.patched_decoder.PatchedDecoderFinetuneModel`.

**Batch Preparation Helpers:**
- Purpose: Convert raw tabular sequences into shapes expected by TimesFM/Pax training and evaluation steps.
- Examples: `src/train.py` `random_masking()`, `prepare_batch_data()`, `reshape_batch()`, `preprocess_csv()`
- Pattern: Functional data-preparation helpers shared across training and evaluation modules.

**Evaluation Metric Helpers:**
- Purpose: Keep metrics reusable across rolling evaluation and crypto backtesting paths.
- Examples: `src/evaluate_forecast.py` `mape()`, `smape()`, `directional_accuracy()`; `src/utils.py` `get_accuracy()`, `mse()`
- Pattern: Stateless numeric helper functions operating on `numpy` or JAX arrays.

**SQLite Persistence Boundary:**
- Purpose: Isolate the crypto backtest's storage responsibility from the forecasting logic.
- Examples: `src/crypto_minute_backtest.py` `ensure_schema()`, `store_candles()`, `load_candles()`, `save_backtest()`
- Pattern: Plain SQL functions around a `sqlite3.Connection`, with forecasting code passing in already-materialized frames and metrics.

## Entry Points

**Fine-Tuning CLI:**
- Location: `src/main.py`
- Triggers: `python src/main.py --workdir ... --config configs/fine_tuning.py --dataset_path ...`
- Responsibilities: Validate required flags, load config, construct base TimesFM checkpoint, and dispatch to training or checkpoint evaluation.

**Single-Series Forecast CLI:**
- Location: `src/run_forecast.py`
- Triggers: `python src/run_forecast.py ...` and the default container start from `Dockerfile`
- Responsibilities: Load one source series, build a forecasting model, execute one forecast, and print or save the result.

**Rolling Evaluation CLI:**
- Location: `src/evaluate_forecast.py`
- Triggers: `python src/evaluate_forecast.py ...`
- Responsibilities: Reuse the forecasting helpers to run repeated windows and summarize forecast accuracy.

**Crypto Backtest / Live CLI:**
- Location: `src/crypto_minute_backtest.py`
- Triggers: `python src/crypto_minute_backtest.py ...` or `scripts/run_crypto_backtest.ps1`
- Responsibilities: Fetch Binance candles, maintain the SQLite schema, run batched forecasts, and emit either backtest metrics or a live forecast table.

**Windows Bootstrap Wrapper:**
- Location: `scripts/setup_windows.ps1`
- Triggers: Direct PowerShell execution
- Responsibilities: Enforce Python 3.10, create `.venv`, upgrade `pip`, and install `requirements.inference.txt`.

**Legacy Mock-Trading CLI:**
- Location: `src/mock_trading.py`
- Triggers: `python src/mock_trading.py ...`
- Responsibilities: Load a historical panel, generate long/short positions from TimesFM forecasts, and save per-horizon position CSVs.

## Error Handling

**Strategy:** Fail fast in each script, with validation near the input boundary and minimal recovery once execution starts.

**Patterns:**
- CLI layers use `argparse` mutual-exclusion groups in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`, and required `absl.flags` in `src/main.py`.
- Data loaders raise `ValueError` for missing columns, empty datasets, too-short series, and invalid evaluation spans in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Operational PowerShell scripts wrap external calls in `Invoke-CheckedCommand` and throw immediately on non-zero exit codes.
- Training code in `src/train.py` and `src/evaluation.py` explicitly guards batch/device divisibility, then relies on lower-level JAX/Pax/TimesFM exceptions for deeper runtime failures.

## Cross-Cutting Concerns

**Logging:** `src/train.py` and `src/evaluation.py` create file and console loggers under `workdir/logs/<timestamp>/`; the newer CLI scripts print summaries directly to stdout; PowerShell scripts use `Write-Host`.

**Validation:** Input validation is concentrated at entrypoints. `configs/fine_tuning.py` supplies the reusable fine-tuning defaults, CLI scripts validate file columns and minimum lengths, and training/evaluation code validates device-compatible batch sizes before running JAX work.

**Authentication:** No repo-managed auth layer is implemented. External access uses public endpoints or repository ids through `yfinance`, Binance HTTP requests in `src/crypto_minute_backtest.py`, and Hugging Face checkpoint resolution through `timesfm`.

---

*Architecture analysis: 2026-04-13*
