# Coding Conventions

**Analysis Date:** 2026-04-13

## Naming Patterns

**Files:**
- Use `snake_case.py` for Python modules in `src/` and `configs/`, for example `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/mock_trading_utils.py`, and `configs/fine_tuning.py`.
- Use descriptive action-oriented names for entry scripts in `scripts/`, for example `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Keep notebook names aligned with the script vocabulary when notebooks are present, as in `src/mock_trading.ipynb`.

**Functions:**
- Use `snake_case` for Python functions, for example `parse_args`, `load_series_from_csv`, `train_and_evaluate`, `restore_and_evaluate`, and `directional_accuracy` in `src/run_forecast.py`, `src/train.py`, and `src/evaluate_forecast.py`.
- Use verb-led helper names for CLI and data-pipeline code, for example `build_model`, `ensure_schema`, `store_candles`, `prepare_live_frame`, and `save_backtest` in `src/crypto_minute_backtest.py`.
- Use PowerShell approved verb style with a hyphen for helper functions, as in `Invoke-CheckedCommand` in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.

**Variables:**
- Use `snake_case` for variables and parameters throughout Python modules, for example `context_len`, `output_csv`, `prediction_rows`, `train_loader`, and `local_batch_size`.
- Use `UPPER_SNAKE_CASE` for module constants, for example `DEFAULT_REPO_ID` in `src/run_forecast.py` and `BINANCE_KLINES_URL`, `ONE_MINUTE_MS`, `MINUTES_PER_YEAR` in `src/crypto_minute_backtest.py`.
- Keep CLI option names kebab-case at the command boundary and translate them into snake_case attributes through `argparse`, for example `--context-len` -> `args.context_len` in `src/run_forecast.py` and `src/evaluate_forecast.py`.

**Types:**
- Use `PascalCase` for classes and config-like types, for example `PatchedDecoderFinetuneFinance` in `src/train.py` and `TrainState` in `src/train_flax.py`.
- Use built-in generic annotations in newer scripts, for example `list[dict[str, float | int | str]]` in `src/evaluate_forecast.py` and `tuple[pd.DataFrame, float]` in `src/crypto_minute_backtest.py`.
- Expect mixed typing depth across the repo: newer forecasting scripts are annotated, while legacy training code in `src/train.py`, `src/evaluation.py`, and `src/mock_trading_utils.py` remains partially typed or untyped.

## Code Style

**Formatting:**
- No formatter config is committed at the repo root or approved roots: no `pyproject.toml`, `.editorconfig`, `setup.cfg`, `.flake8`, `ruff.toml`, or `.ruff.toml` was found beside `README.md`, `Dockerfile`, `src/`, `configs/`, or `scripts/`.
- Follow the dominant current style in the newer forecasting scripts: 4-space indentation, multiline argument lists with trailing commas, and blank lines between import groups, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Preserve local legacy style when touching older training/config files that use 2-space indentation or mixed spacing, such as `src/main.py` and `configs/fine_tuning.py`, instead of reformatting them opportunistically.
- Strings are mixed. Newer files lean on double quotes in `src/run_forecast.py` and `src/crypto_minute_backtest.py`; older files lean on single quotes in `src/train.py`, `src/evaluation.py`, and `src/mock_trading_utils.py`. Match the file you are editing.
- Semicolons are not used in Python. PowerShell files also avoid statement-terminating semicolons in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.

**Linting:**
- No lint config or lint command is committed in the repo root, `configs/`, `scripts/`, or `src/`.
- Treat the newer CLI modules as the clearest style reference for new work near inference/backtesting code: `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Avoid widening legacy exceptions. For example, `from utils import *` appears in `src/train_flax.py`, but other modules use explicit imports and that is the safer pattern for new code.

## Import Organization

**Order:**
1. Standard library imports first, for example `argparse`, `os`, `sqlite3`, `datetime`, and `pathlib` in `src/run_forecast.py` and `src/crypto_minute_backtest.py`.
2. Third-party imports next, for example `numpy`, `pandas`, `jax`, `tensorflow`, `timesfm`, and `ml_collections` in `src/evaluate_forecast.py`, `src/train.py`, and `configs/fine_tuning.py`.
3. Local module imports last, for example `from run_forecast import ...` in `src/evaluate_forecast.py`, `from evaluate_forecast import ...` in `src/crypto_minute_backtest.py`, and `import train` / `import evaluation` in `src/main.py`.

**Grouping:**
- Newer files separate import groups with a blank line, as in `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Older training modules are only loosely organized and contain a few legacy issues such as duplicate imports (`gc` appears twice in `src/train.py` and `src/evaluation.py`). Do not copy those issues into new code.
- Local imports are file-based and assume execution from the repository root or the `src/` directory rather than an installed package layout.

**Path Aliases:**
- No import alias system is configured. There is no package alias such as `@/` or a Python package namespace configured in the repo.
- Import sibling helpers directly by module filename, for example `from run_forecast import build_model` in `src/evaluate_forecast.py` and `from train import preprocess_csv` in `src/evaluation.py`.

## Error Handling

**Patterns:**
- Raise `ValueError` for invalid CLI input, missing data, and impossible runtime preconditions in the newer scripts, for example in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Use `try` / `finally` to close resources at the boundary layer, as in the SQLite connection cleanup in `src/crypto_minute_backtest.py`.
- In PowerShell, stop on all errors with `$ErrorActionPreference = "Stop"` and wrap external process execution in `Invoke-CheckedCommand`, as in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Legacy training/evaluation code in `src/train.py` and `src/evaluation.py` mostly validates with `ValueError` and relies on logs rather than structured recovery or custom exception classes.

**Error Types:**
- Throw on missing or malformed external data, for example empty Yahoo responses or missing CSV columns in `src/run_forecast.py`.
- Throw on impossible model/data shape combinations, for example insufficient context or invalid batch/device divisibility in `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/train.py`, and `src/evaluation.py`.
- No custom exception hierarchy is defined in `src/`, `configs/`, or `scripts/`. New errors should stay simple unless a repeated pattern emerges.

## Logging

**Framework:**
- User-facing CLI flows print directly to stdout with `print(...)` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and `src/mock_trading.py`.
- Long-running training/evaluation flows use the standard library `logging` module with file and console handlers in `src/train.py` and `src/evaluation.py`.
- PowerShell wrappers use `Write-Host` for progress messages in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.

**Patterns:**
- Prefer concise table-style terminal output for inference and backtest scripts, usually followed by an optional `"Saved to"` line, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- In training code, attach both a file handler and console handler under a timestamped `logs/` directory rooted at the user-provided workdir, as in `src/train.py` and `src/evaluation.py`.
- Structured logging is not used. If you add logging in script-style code, keep it simple and consistent with nearby files instead of introducing a new framework.

## Comments

**When to Comment:**
- Use short inline comments to explain operational context or caveats, for example the `# TODO` notes in `src/main.py` and `src/train.py`, the forward-fill notes in `src/mock_trading_utils.py`, and the checkpoint caveats at the top of `src/train_flax.py`.
- Use comments to explain non-obvious model/runtime constraints rather than restating code, as seen in `configs/fine_tuning.py`, `src/train.py`, and `src/train_flax.py`.
- The newer forecasting scripts keep comments sparse and rely more on clear helper names; follow that lighter style in files near `src/run_forecast.py` and `src/evaluate_forecast.py`.

**JSDoc/TSDoc:**
- Python docstrings are common in the legacy utility and training modules, especially `src/utils.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, and `configs/fine_tuning.py`.
- Newer CLI modules such as `src/run_forecast.py`, `src/evaluate_forecast.py`, and large parts of `src/crypto_minute_backtest.py` favor type hints and readable function names over docstrings.
- When extending the legacy training stack, continue using docstrings on non-trivial helpers. When extending the newer CLI scripts, docstrings are optional unless the behavior is not obvious from the signature and name.

**TODO Comments:**
- TODOs are freeform inline comments rather than ticket-linked annotations, for example `# TODO: why does setting horizon_len to 512 not work` in `src/main.py` and `#TODO: optimize this for parallelization` in `src/train.py`.
- If you add a TODO, keep it specific and colocated with the constraint it describes. There is no enforced owner or issue-number format in the repo.

## Function Design

**Size:**
- Newer forecasting files break work into small focused helpers such as `load_series_from_csv`, `infer_future_index`, `format_results`, `fetch_binance_klines`, and `run_live_forecast` in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Legacy training functions in `src/train.py` and `src/train_flax.py` are much larger and orchestrate full training loops. Treat that as inherited code, not the preferred shape for new utility logic.

**Parameters:**
- CLI entrypoints centralize user inputs in `argparse.Namespace` objects returned by `parse_args()` in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Pure helpers usually take explicit scalar/dataframe parameters rather than passing large option objects, for example `mape`, `smape`, `directional_accuracy`, `annual_returns`, and `sharpe_ratio`.
- Legacy training helpers often expose many positional parameters with defaults, for example `prepare_batch_data(...)` in `src/train.py` and `eval_step(...)` in `src/train_flax.py`. Do not expand that pattern further unless you are staying inside the training subsystem.

**Return Values:**
- Use explicit returns, often with tuples or dictionaries for multi-value results, for example `tuple[pd.DataFrame, float]` from `run_live_forecast` and metrics dictionaries from `evaluate_series` and `run_backtest`.
- Use early guard clauses and return or raise immediately when preconditions fail, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.

## Module Design

**Exports:**
- The codebase is script-oriented rather than package-oriented. Modules expose plain top-level functions and constants and are imported directly by filename from other modules in `src/`.
- CLI-capable modules end with `main()` plus `if __name__ == "__main__": main()` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, and `src/mock_trading.py`.
- Shared reusable logic sits in ordinary modules such as `src/utils.py` and `src/mock_trading_utils.py` rather than class-heavy service objects.

**Barrel Files:**
- No barrel files or package `__init__.py` exports are used in `src/`, `configs/`, or `scripts/`.
- When adding shared code, place it in a directly imported module under `src/` and import it explicitly from callers, matching `src/evaluate_forecast.py` and `src/crypto_minute_backtest.py`.

---

*Convention analysis: 2026-04-13*
