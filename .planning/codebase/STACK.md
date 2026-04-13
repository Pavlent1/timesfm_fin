# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- Python 3.10 - All executable application code under `src/`, hyperparameter config in `configs/fine_tuning.py`, and the container runtime in `Dockerfile`

**Secondary:**
- PowerShell - Windows bootstrap and Docker wrapper scripts in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`
- Dockerfile syntax - Containerized inference runtime defined in `Dockerfile`

## Runtime

**Environment:**
- CPython 3.10 - Required by `README.md`, enforced by `scripts/setup_windows.ps1`, and used as the base image in `Dockerfile`
- JAX/PAX TimesFM runtime - Used by training and checkpoint-backed inference in `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/run_forecast.py`, and `src/crypto_minute_backtest.py`
- Linux, WSL, or Docker is the practical runtime for the JAX/PAX checkpoint path; `README.md` explicitly positions Docker as the recommended Windows path

**Package Manager:**
- `pip` - Dependencies are installed from `requirements.inference.txt` and direct `pip install` commands in `README.md` and `Dockerfile`
- Lockfile: missing

## Frameworks

**Core:**
- TimesFM 1.3.0 - Forecasting model runtime and checkpoint loader used in `src/run_forecast.py`, `src/main.py`, `src/mock_trading.py`, `src/train.py`, and `src/evaluation.py`
- JAX + PaxML/Praxis ecosystem - Fine-tuning and evaluation stack used in `src/train.py`, `src/evaluation.py`, and the deprecated alternative path in `src/train_flax.py`

**Testing:**
- Not detected - No dedicated test runner or test files are present in the inspected roots `src/`, `configs/`, and `scripts/`

**Build/Dev:**
- Docker - Container build and execution path for inference and crypto backtests via `Dockerfile` and `scripts/run_crypto_backtest.ps1`
- Python `venv` - Local environment bootstrap path created by `scripts/setup_windows.ps1`
- `argparse` and `absl.flags` - CLI/runtime configuration for inference entrypoints in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and training entrypoints in `src/main.py` and `src/mock_trading.py`

## Key Dependencies

**Critical:**
- `timesfm==1.3.0` - Pinned inference runtime in `requirements.inference.txt`; also referenced throughout `README.md` and loaded directly in `src/run_forecast.py`
- `yfinance>=0.2.54,<1.0` - Yahoo Finance data client used by `src/run_forecast.py` and transitively by `src/evaluate_forecast.py`
- `pandas>=2.2,<3.0` - Core tabular I/O and output formatting library used across `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/train.py`, and `src/evaluation.py`
- `numpy>=1.26,<2.0` - Numeric array processing used across inference, backtesting, training, and evaluation code in `src/`
- `jax` - Device runtime for model execution and pmapped training/evaluation in `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, and `src/mock_trading.py`

**Infrastructure:**
- `paxml` and `praxis` - Training orchestration, checkpoints, learners, and layer configuration in `src/train.py` and `src/evaluation.py`
- `tensorflow` and `clu` - Dataset handling, summaries, and metric writers in `src/train.py`, `src/evaluation.py`, and `src/train_flax.py`
- `ml_collections` - Hyperparameter config loading in `configs/fine_tuning.py` and `src/main.py`
- Python standard library `sqlite3` and `urllib.request` - Local persistence and Binance REST access in `src/crypto_minute_backtest.py`

## Configuration

**Environment:**
- Runtime configuration is primarily CLI-driven, not `.env`-driven; entrypoints accept flags such as `--ticker`, `--csv`, `--repo-id`, `--backend`, `--db-path`, `--workdir`, and `--dataset_path` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, and `src/mock_trading.py`
- Hyperparameters for fine-tuning live in `configs/fine_tuning.py`
- `src/run_forecast.py` sets `JAX_PLATFORMS=cpu` programmatically when `--backend cpu` is used
- No `.env` files were detected at the repo root during this analysis

**Build:**
- `Dockerfile` - Reproducible inference container based on `python:3.10-slim`
- `requirements.inference.txt` - Pinned inference dependency set
- `scripts/setup_windows.ps1` - Local Windows bootstrap script for `.venv`
- `scripts/run_crypto_backtest.ps1` - Dockerized execution wrapper for `src/crypto_minute_backtest.py`

## Platform Requirements

**Development:**
- Python 3.10 is required; `scripts/setup_windows.ps1` aborts on non-3.10 interpreters
- `pip` and `venv` are required for local installs
- Docker is the supported Windows execution path for the finance checkpoint and for the crypto backtest wrapper in `scripts/run_crypto_backtest.ps1`
- Training and evaluation flows expect a local dataset path and a writable work directory, passed to `src/main.py` and `src/mock_trading.py`

**Production:**
- No always-on service or hosted deployment target is defined in the inspected files
- The operational shape is batch/CLI execution: local Python commands or a Docker container running `src/run_forecast.py` or `src/crypto_minute_backtest.py`

---

*Stack analysis: 2026-04-13*
