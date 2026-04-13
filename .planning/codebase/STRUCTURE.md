# Codebase Structure

**Analysis Date:** 2026-04-13

## Directory Layout

```text
timesfm_fin/
|-- configs/                    # Reusable training configuration modules
|   `-- fine_tuning.py          # Default fine-tuning hyperparameters and metric list
|-- scripts/                    # Windows-oriented operational wrappers
|   |-- run_crypto_backtest.ps1 # Docker launcher for the crypto backtest/live CLI
|   `-- setup_windows.ps1       # Python 3.10 and venv bootstrap for inference
|-- src/                        # Flat Python source tree for training, inference, and experiments
|   |-- main.py                 # Fine-tuning and evaluation entrypoint
|   |-- train.py                # Pax/JAX training loop and finance decoder adapter
|   |-- evaluation.py           # Checkpoint restore and evaluation loop
|   |-- run_forecast.py         # Single-series forecast CLI and shared model helpers
|   |-- evaluate_forecast.py    # Rolling forecast benchmark CLI
|   |-- crypto_minute_backtest.py # Binance + SQLite backtest/live forecast CLI
|   |-- mock_trading.py         # Legacy mock-trading script
|   |-- mock_trading_utils.py   # Dataset loading helpers for mock trading
|   |-- train_flax.py           # Deprecated alternative training implementation
|   |-- utils.py                # Shared training metrics and optimizer helpers
|   `-- mock_trading.ipynb      # Notebook exploration for trading analysis
|-- Dockerfile                  # Containerized inference/backtest entry definition
|-- requirements.inference.txt  # Minimal pip dependencies for inference workflows
`-- README.md                   # Human-readable setup and execution guide
```

## Directory Purposes

**`src/`:**
- Purpose: Holds all Python application code in a single flat namespace.
- Contains: CLI scripts, training logic, evaluation logic, legacy experiments, a notebook, and helper modules.
- Key files: `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`
- Subdirectories: `src/__pycache__/` is generated Python bytecode and is not part of the intended source layout.

**`configs/`:**
- Purpose: Stores reusable Python config modules that are loaded by the training entrypoint.
- Contains: `ml_collections.ConfigDict` definitions.
- Key files: `configs/fine_tuning.py`
- Subdirectories: None.

**`scripts/`:**
- Purpose: Stores PowerShell wrappers for local setup and Docker-backed execution from Windows.
- Contains: `.ps1` launcher and bootstrap scripts.
- Key files: `scripts/run_crypto_backtest.ps1`, `scripts/setup_windows.ps1`
- Subdirectories: None.

## Key File Locations

**Entry Points:**
- `src/main.py`: Main `absl` entrypoint for fine-tuning and evaluation against a user-supplied dataset and work directory.
- `src/run_forecast.py`: Main inference CLI and the process started by `Dockerfile`.
- `src/evaluate_forecast.py`: Rolling evaluation CLI for tickers or a single CSV series.
- `src/crypto_minute_backtest.py`: Binance-minute backtest and live-forecast CLI with SQLite persistence.
- `src/mock_trading.py`: Legacy mock-trading CLI for generating position CSVs.
- `scripts/run_crypto_backtest.ps1`: Windows wrapper that builds the container and launches `src/crypto_minute_backtest.py`.
- `scripts/setup_windows.ps1`: Windows bootstrapper for the local inference environment.

**Configuration:**
- `configs/fine_tuning.py`: Central fine-tuning hyperparameters, dataset path placeholder, and metric names.
- `requirements.inference.txt`: Minimal dependency set for the inference-oriented path.
- `Dockerfile`: Runtime packaging for containerized forecast and backtest execution.
- `README.md`: Setup guidance, command examples, and operational notes for the current repo state.

**Core Logic:**
- `src/train.py`: Main fine-tuning implementation, training/evaluation steps, learner setup, and checkpoint save logic.
- `src/evaluation.py`: Checkpoint restoration flow for multi-horizon evaluation.
- `src/run_forecast.py`: Shared inference helpers for loading data, building the model, and formatting output.
- `src/evaluate_forecast.py`: Rolling evaluation metrics and result formatting.
- `src/crypto_minute_backtest.py`: Binance ingestion, SQLite schema management, rolling forecast execution, and live forecast formatting.
- `src/utils.py`: JAX/Optax numeric helpers used by the training-oriented code.

**Testing:**
- Not detected. There are no `tests/` directories, `test_*.py` files, or `*_test.py`/`*_spec.py` files in the approved roots or the inspected repo-root context files.

**Documentation:**
- `README.md`: Primary project documentation for installation, inference, backtesting, and the legacy training path.

## Naming Conventions

**Files:**
- Use `snake_case.py` for Python modules and scripts: `src/run_forecast.py`, `src/crypto_minute_backtest.py`, `src/mock_trading_utils.py`.
- Use descriptive verb-led script names for executable modules: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`.
- Use `snake_case.ps1` for operational PowerShell scripts: `scripts/setup_windows.ps1`, `scripts/run_crypto_backtest.ps1`.
- Keep configuration files as importable Python modules rather than YAML or JSON: `configs/fine_tuning.py`.
- Notebook artifacts follow the same descriptive naming style: `src/mock_trading.ipynb`.

**Directories:**
- Root code directories are short plural nouns: `src/`, `configs/`, `scripts/`.
- The approved roots are intentionally shallow; there are no feature subpackages under `src/`.

**Special Patterns:**
- `src/main.py` is the only `main.py` style entrypoint and is reserved for the fine-tuning path.
- `run_*.py` files are direct execution scripts rather than library-only modules.
- Helper reuse is currently achieved by importing sibling files directly, so moving a shared function into a new nested package requires import updates across the flat `src/` tree.

## Where to Add New Code

**New Feature:**
- Primary code: `src/`
- Tests: Not established in the current structure; add a new `tests/` root only if you are introducing a real test suite rather than ad hoc scripts.
- Config if needed: `configs/` for reusable training-style settings, or CLI flags directly in the owning `src/*.py` entrypoint for one-off runtime controls.

**New Component/Module:**
- Implementation: Add a new `snake_case.py` module directly under `src/`.
- Types: Keep inline with the owning module; there is no separate types package.
- Tests: Not established; if tests are introduced, place them in a new top-level `tests/` directory rather than mixing them into `src/`.

**New Route/Command:**
- Definition: Add a new standalone CLI module under `src/`, following the existing `run_*.py` or `evaluate_*.py` naming style when the file is directly executable.
- Handler: Keep the main orchestration function in the same `src/*.py` file unless a helper has obvious reuse with another script.
- Tests: Not detected; introducing tests would require creating the convention first.

**Utilities:**
- Shared helpers: Keep training-only helpers in `src/utils.py`.
- Shared inference helpers: Prefer extracting adjacent helper modules under `src/` when a function would otherwise duplicate logic from `src/run_forecast.py` or `src/evaluate_forecast.py`.
- Type definitions: Keep them in the owning module via standard Python annotations.

## Special Directories

**`src/__pycache__/`:**
- Purpose: Generated Python bytecode cache from local script execution.
- Source: Created automatically by Python.
- Committed: No; `.gitignore` ignores `__pycache__/`.

**`outputs/`:**
- Purpose: Default destination for generated forecast CSVs and the SQLite database used by `src/crypto_minute_backtest.py`.
- Source: Produced at runtime by the forecast and backtest scripts.
- Committed: No by default for generated contents; it is an execution artifact directory rather than source code.

---

*Structure analysis: 2026-04-13*
