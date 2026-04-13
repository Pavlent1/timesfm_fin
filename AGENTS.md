# Repository AGENTS

## Purpose

This is the repo-level instruction entrypoint that runtime agents can discover automatically.

## Git Checkpoints

- Create commits on the currently checked out branch at logical checkpoints during multi-step work.
- Keep commits small, focused, and clearly messaged.
- Do not push unless the user explicitly requests it.
- Avoid checkpoint commits while the work is still in a broken mixed half-state unless that is the safest recoverable boundary.

## AgentHelper Routing

When a task creates, edits, moves, reviews, or depends on files under `AgentHelper/`, route into the helper library instructions before making changes.

Also route into the helper library instructions when a task touches files that fall under the approved codebase roots defined in `AgentHelper/ProjectFiles/CodebaseScope.md`, because those files may require description lookup or description maintenance.

Read in this order:

1. `AgentHelper/AgentRelated/AGENTS.template.md`
2. `AgentHelper/AgentRelated/ARCHITECTURE.md`
3. `AgentHelper/ProjectFiles/CodebaseScope.md` when the task touches approved codebase roots, or when project-file descriptions or codebase mapping are relevant
4. Only the relevant folders under `AgentHelper/AgentRelated/AdditionalRules/`

If the task touches a file inside an approved codebase root, check for a matching description under `AgentHelper/ProjectFiles/DescriptionFiles/` before editing when one exists, and update that description when the real file is created, moved, renamed, or materially changed.

## AgentHelper Ownership

- `AgentHelper/AgentRelated/` is the reusable library-owned area.
- `AgentHelper/ProjectFiles/` is the project-specific artifact area for this repository.
- Reusable helper skills live in `AgentHelper/AgentRelated/Skills/`.
- If a reusable helper skill is added, edited, renamed, or removed, refresh the runtime mirror in `.codex/skills/` with `scripts/install-agenthelper-skills.ps1`.

## Notes

- `AgentHelper/AgentRelated/AGENTS.template.md` is a non-active template copy kept for reuse and copy/paste. It is not the auto-discovered repo entrypoint.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**TimesFM Finance Toolkit**

This repository is a brownfield Python toolkit for fine-tuning and running the legacy TimesFM v1 model on financial time-series data. It currently serves researchers and engineers who need CLI-driven forecasting, rolling evaluation, and crypto minute backtesting without turning the project into a hosted trading service.

**Core Value:** Users can run reproducible financial forecasting and backtesting workflows with the supported TimesFM finance checkpoint and clearly understand what is and is not supported.

### Constraints

- **Tech stack**: Python 3.10 plus the legacy TimesFM v1 / JAX / PAX ecosystem - the repository is intentionally aligned to the older checkpoint family.
- **Runtime**: Linux, WSL, or Docker for the supported checkpoint path - native Windows remains an orchestration environment rather than the target runtime.
- **Data**: Fine-tuning depends on private financial datasets - public examples must rely on Yahoo Finance, Binance, or user-provided CSV files.
- **Product shape**: CLI-first workflows only - there is no current web app, background service, or deployment target to build against.
- **Trust boundary**: Remote checkpoints and market data are fetched from external services - reproducibility and provenance need to be made explicit in outputs and docs.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.10 - All executable application code under `src/`, hyperparameter config in `configs/fine_tuning.py`, and the container runtime in `Dockerfile`
- PowerShell - Windows bootstrap and Docker wrapper scripts in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`
- Dockerfile syntax - Containerized inference runtime defined in `Dockerfile`
## Runtime
- CPython 3.10 - Required by `README.md`, enforced by `scripts/setup_windows.ps1`, and used as the base image in `Dockerfile`
- JAX/PAX TimesFM runtime - Used by training and checkpoint-backed inference in `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/run_forecast.py`, and `src/crypto_minute_backtest.py`
- Linux, WSL, or Docker is the practical runtime for the JAX/PAX checkpoint path; `README.md` explicitly positions Docker as the recommended Windows path
- `pip` - Dependencies are installed from `requirements.inference.txt` and direct `pip install` commands in `README.md` and `Dockerfile`
- Lockfile: missing
## Frameworks
- TimesFM 1.3.0 - Forecasting model runtime and checkpoint loader used in `src/run_forecast.py`, `src/main.py`, `src/mock_trading.py`, `src/train.py`, and `src/evaluation.py`
- JAX + PaxML/Praxis ecosystem - Fine-tuning and evaluation stack used in `src/train.py`, `src/evaluation.py`, and the deprecated alternative path in `src/train_flax.py`
- Not detected - No dedicated test runner or test files are present in the inspected roots `src/`, `configs/`, and `scripts/`
- Docker - Container build and execution path for inference and crypto backtests via `Dockerfile` and `scripts/run_crypto_backtest.ps1`
- Python `venv` - Local environment bootstrap path created by `scripts/setup_windows.ps1`
- `argparse` and `absl.flags` - CLI/runtime configuration for inference entrypoints in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and training entrypoints in `src/main.py` and `src/mock_trading.py`
## Key Dependencies
- `timesfm==1.3.0` - Pinned inference runtime in `requirements.inference.txt`; also referenced throughout `README.md` and loaded directly in `src/run_forecast.py`
- `yfinance>=0.2.54,<1.0` - Yahoo Finance data client used by `src/run_forecast.py` and transitively by `src/evaluate_forecast.py`
- `pandas>=2.2,<3.0` - Core tabular I/O and output formatting library used across `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/train.py`, and `src/evaluation.py`
- `numpy>=1.26,<2.0` - Numeric array processing used across inference, backtesting, training, and evaluation code in `src/`
- `jax` - Device runtime for model execution and pmapped training/evaluation in `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, and `src/mock_trading.py`
- `paxml` and `praxis` - Training orchestration, checkpoints, learners, and layer configuration in `src/train.py` and `src/evaluation.py`
- `tensorflow` and `clu` - Dataset handling, summaries, and metric writers in `src/train.py`, `src/evaluation.py`, and `src/train_flax.py`
- `ml_collections` - Hyperparameter config loading in `configs/fine_tuning.py` and `src/main.py`
- Python standard library `sqlite3` and `urllib.request` - Local persistence and Binance REST access in `src/crypto_minute_backtest.py`
## Configuration
- Runtime configuration is primarily CLI-driven, not `.env`-driven; entrypoints accept flags such as `--ticker`, `--csv`, `--repo-id`, `--backend`, `--db-path`, `--workdir`, and `--dataset_path` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, and `src/mock_trading.py`
- Hyperparameters for fine-tuning live in `configs/fine_tuning.py`
- `src/run_forecast.py` sets `JAX_PLATFORMS=cpu` programmatically when `--backend cpu` is used
- No `.env` files were detected at the repo root during this analysis
- `Dockerfile` - Reproducible inference container based on `python:3.10-slim`
- `requirements.inference.txt` - Pinned inference dependency set
- `scripts/setup_windows.ps1` - Local Windows bootstrap script for `.venv`
- `scripts/run_crypto_backtest.ps1` - Dockerized execution wrapper for `src/crypto_minute_backtest.py`
## Platform Requirements
- Python 3.10 is required; `scripts/setup_windows.ps1` aborts on non-3.10 interpreters
- `pip` and `venv` are required for local installs
- Docker is the supported Windows execution path for the finance checkpoint and for the crypto backtest wrapper in `scripts/run_crypto_backtest.ps1`
- Training and evaluation flows expect a local dataset path and a writable work directory, passed to `src/main.py` and `src/mock_trading.py`
- No always-on service or hosted deployment target is defined in the inspected files
- The operational shape is batch/CLI execution: local Python commands or a Docker container running `src/run_forecast.py` or `src/crypto_minute_backtest.py`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Use `snake_case.py` for Python modules in `src/` and `configs/`, for example `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/mock_trading_utils.py`, and `configs/fine_tuning.py`.
- Use descriptive action-oriented names for entry scripts in `scripts/`, for example `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Keep notebook names aligned with the script vocabulary when notebooks are present, as in `src/mock_trading.ipynb`.
- Use `snake_case` for Python functions, for example `parse_args`, `load_series_from_csv`, `train_and_evaluate`, `restore_and_evaluate`, and `directional_accuracy` in `src/run_forecast.py`, `src/train.py`, and `src/evaluate_forecast.py`.
- Use verb-led helper names for CLI and data-pipeline code, for example `build_model`, `ensure_schema`, `store_candles`, `prepare_live_frame`, and `save_backtest` in `src/crypto_minute_backtest.py`.
- Use PowerShell approved verb style with a hyphen for helper functions, as in `Invoke-CheckedCommand` in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Use `snake_case` for variables and parameters throughout Python modules, for example `context_len`, `output_csv`, `prediction_rows`, `train_loader`, and `local_batch_size`.
- Use `UPPER_SNAKE_CASE` for module constants, for example `DEFAULT_REPO_ID` in `src/run_forecast.py` and `BINANCE_KLINES_URL`, `ONE_MINUTE_MS`, `MINUTES_PER_YEAR` in `src/crypto_minute_backtest.py`.
- Keep CLI option names kebab-case at the command boundary and translate them into snake_case attributes through `argparse`, for example `--context-len` -> `args.context_len` in `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Use `PascalCase` for classes and config-like types, for example `PatchedDecoderFinetuneFinance` in `src/train.py` and `TrainState` in `src/train_flax.py`.
- Use built-in generic annotations in newer scripts, for example `list[dict[str, float | int | str]]` in `src/evaluate_forecast.py` and `tuple[pd.DataFrame, float]` in `src/crypto_minute_backtest.py`.
- Expect mixed typing depth across the repo: newer forecasting scripts are annotated, while legacy training code in `src/train.py`, `src/evaluation.py`, and `src/mock_trading_utils.py` remains partially typed or untyped.
## Code Style
- No formatter config is committed at the repo root or approved roots: no `pyproject.toml`, `.editorconfig`, `setup.cfg`, `.flake8`, `ruff.toml`, or `.ruff.toml` was found beside `README.md`, `Dockerfile`, `src/`, `configs/`, or `scripts/`.
- Follow the dominant current style in the newer forecasting scripts: 4-space indentation, multiline argument lists with trailing commas, and blank lines between import groups, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Preserve local legacy style when touching older training/config files that use 2-space indentation or mixed spacing, such as `src/main.py` and `configs/fine_tuning.py`, instead of reformatting them opportunistically.
- Strings are mixed. Newer files lean on double quotes in `src/run_forecast.py` and `src/crypto_minute_backtest.py`; older files lean on single quotes in `src/train.py`, `src/evaluation.py`, and `src/mock_trading_utils.py`. Match the file you are editing.
- Semicolons are not used in Python. PowerShell files also avoid statement-terminating semicolons in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- No lint config or lint command is committed in the repo root, `configs/`, `scripts/`, or `src/`.
- Treat the newer CLI modules as the clearest style reference for new work near inference/backtesting code: `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Avoid widening legacy exceptions. For example, `from utils import *` appears in `src/train_flax.py`, but other modules use explicit imports and that is the safer pattern for new code.
## Import Organization
- Newer files separate import groups with a blank line, as in `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Older training modules are only loosely organized and contain a few legacy issues such as duplicate imports (`gc` appears twice in `src/train.py` and `src/evaluation.py`). Do not copy those issues into new code.
- Local imports are file-based and assume execution from the repository root or the `src/` directory rather than an installed package layout.
- No import alias system is configured. There is no package alias such as `@/` or a Python package namespace configured in the repo.
- Import sibling helpers directly by module filename, for example `from run_forecast import build_model` in `src/evaluate_forecast.py` and `from train import preprocess_csv` in `src/evaluation.py`.
## Error Handling
- Raise `ValueError` for invalid CLI input, missing data, and impossible runtime preconditions in the newer scripts, for example in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Use `try` / `finally` to close resources at the boundary layer, as in the SQLite connection cleanup in `src/crypto_minute_backtest.py`.
- In PowerShell, stop on all errors with `$ErrorActionPreference = "Stop"` and wrap external process execution in `Invoke-CheckedCommand`, as in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Legacy training/evaluation code in `src/train.py` and `src/evaluation.py` mostly validates with `ValueError` and relies on logs rather than structured recovery or custom exception classes.
- Throw on missing or malformed external data, for example empty Yahoo responses or missing CSV columns in `src/run_forecast.py`.
- Throw on impossible model/data shape combinations, for example insufficient context or invalid batch/device divisibility in `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/train.py`, and `src/evaluation.py`.
- No custom exception hierarchy is defined in `src/`, `configs/`, or `scripts/`. New errors should stay simple unless a repeated pattern emerges.
## Logging
- User-facing CLI flows print directly to stdout with `print(...)` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and `src/mock_trading.py`.
- Long-running training/evaluation flows use the standard library `logging` module with file and console handlers in `src/train.py` and `src/evaluation.py`.
- PowerShell wrappers use `Write-Host` for progress messages in `scripts/setup_windows.ps1` and `scripts/run_crypto_backtest.ps1`.
- Prefer concise table-style terminal output for inference and backtest scripts, usually followed by an optional `"Saved to"` line, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- In training code, attach both a file handler and console handler under a timestamped `logs/` directory rooted at the user-provided workdir, as in `src/train.py` and `src/evaluation.py`.
- Structured logging is not used. If you add logging in script-style code, keep it simple and consistent with nearby files instead of introducing a new framework.
## Comments
- Use short inline comments to explain operational context or caveats, for example the `# TODO` notes in `src/main.py` and `src/train.py`, the forward-fill notes in `src/mock_trading_utils.py`, and the checkpoint caveats at the top of `src/train_flax.py`.
- Use comments to explain non-obvious model/runtime constraints rather than restating code, as seen in `configs/fine_tuning.py`, `src/train.py`, and `src/train_flax.py`.
- The newer forecasting scripts keep comments sparse and rely more on clear helper names; follow that lighter style in files near `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Python docstrings are common in the legacy utility and training modules, especially `src/utils.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, and `configs/fine_tuning.py`.
- Newer CLI modules such as `src/run_forecast.py`, `src/evaluate_forecast.py`, and large parts of `src/crypto_minute_backtest.py` favor type hints and readable function names over docstrings.
- When extending the legacy training stack, continue using docstrings on non-trivial helpers. When extending the newer CLI scripts, docstrings are optional unless the behavior is not obvious from the signature and name.
- TODOs are freeform inline comments rather than ticket-linked annotations, for example `# TODO: why does setting horizon_len to 512 not work` in `src/main.py` and `#TODO: optimize this for parallelization` in `src/train.py`.
- If you add a TODO, keep it specific and colocated with the constraint it describes. There is no enforced owner or issue-number format in the repo.
## Function Design
- Newer forecasting files break work into small focused helpers such as `load_series_from_csv`, `infer_future_index`, `format_results`, `fetch_binance_klines`, and `run_live_forecast` in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Legacy training functions in `src/train.py` and `src/train_flax.py` are much larger and orchestrate full training loops. Treat that as inherited code, not the preferred shape for new utility logic.
- CLI entrypoints centralize user inputs in `argparse.Namespace` objects returned by `parse_args()` in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Pure helpers usually take explicit scalar/dataframe parameters rather than passing large option objects, for example `mape`, `smape`, `directional_accuracy`, `annual_returns`, and `sharpe_ratio`.
- Legacy training helpers often expose many positional parameters with defaults, for example `prepare_batch_data(...)` in `src/train.py` and `eval_step(...)` in `src/train_flax.py`. Do not expand that pattern further unless you are staying inside the training subsystem.
- Use explicit returns, often with tuples or dictionaries for multi-value results, for example `tuple[pd.DataFrame, float]` from `run_live_forecast` and metrics dictionaries from `evaluate_series` and `run_backtest`.
- Use early guard clauses and return or raise immediately when preconditions fail, as in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
## Module Design
- The codebase is script-oriented rather than package-oriented. Modules expose plain top-level functions and constants and are imported directly by filename from other modules in `src/`.
- CLI-capable modules end with `main()` plus `if __name__ == "__main__": main()` in `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, and `src/mock_trading.py`.
- Shared reusable logic sits in ordinary modules such as `src/utils.py` and `src/mock_trading_utils.py` rather than class-heavy service objects.
- No barrel files or package `__init__.py` exports are used in `src/`, `configs/`, or `scripts/`.
- When adding shared code, place it in a directly imported module under `src/` and import it explicitly from callers, matching `src/evaluate_forecast.py` and `src/crypto_minute_backtest.py`.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Source lives in a flat `src/` module namespace rather than a Python package, so files import each other by filename such as `import train` and `from run_forecast import build_model`.
- Training and evaluation code in `src/main.py`, `src/train.py`, and `src/evaluation.py` is tightly coupled to TimesFM v1, JAX, PaxML, and Praxis.
- Inference and benchmarking code in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py` forms a lighter CLI-oriented path with shared model-construction helpers.
- Operational entry from Windows is delegated to `scripts/*.ps1`, while container execution is defined in `Dockerfile`.
## Layers
- Purpose: Parse CLI arguments or flags, select execution mode, and hand off to the appropriate pipeline.
- Location: `src/main.py`, `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/mock_trading.py`, `scripts/run_crypto_backtest.ps1`, `scripts/setup_windows.ps1`, `Dockerfile`
- Contains: `argparse` CLIs, `absl.flags` entrypoints, Docker startup configuration, and PowerShell wrappers.
- Depends on: Training, inference, evaluation, and data helper modules in `src/`; root packaging files such as `Dockerfile` and `requirements.inference.txt`.
- Used by: Developers running `python ...`, `docker run ...`, or the PowerShell wrapper scripts.
- Purpose: Convert price-history CSVs into training/evaluation batches, wrap the upstream TimesFM decoder for finance fine-tuning, and run replicated training plus checkpointing.
- Location: `src/train.py`, `src/evaluation.py`, `configs/fine_tuning.py`, `src/utils.py`
- Contains: Dataset preprocessing, batch reshaping, learner construction, custom model subclassing, `jax.pmap` training/evaluation steps, TensorBoard logging, and checkpoint save/restore flows.
- Depends on: `timesfm`, `jax`, `tensorflow`, `paxml`, `praxis`, and the config module `configs/fine_tuning.py`.
- Used by: `src/main.py` for normal training and checkpoint evaluation runs.
- Purpose: Build TimesFM checkpoints for prediction, load one or more time series, run forecasts, and compute rolling evaluation metrics.
- Location: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`
- Contains: Yahoo Finance loaders, CSV loaders, future-index inference, TimesFM model factory logic, rolling window evaluation, Binance fetch/persist logic, and SQLite-backed result storage.
- Depends on: `timesfm`, `numpy`, `pandas`, public data APIs, and helper reuse across `src/run_forecast.py` and `src/evaluate_forecast.py`.
- Used by: Direct CLI runs, `Dockerfile` container entry, and `scripts/run_crypto_backtest.ps1`.
- Purpose: Keep older or ad hoc workflows that are adjacent to, but not central to, the current forecast/backtest path.
- Location: `src/train_flax.py`, `src/mock_trading.py`, `src/mock_trading_utils.py`, `src/mock_trading.ipynb`
- Contains: A deprecated Flax-based training implementation, a mock-trading signal generator, dataset loading helpers, and notebook-based exploration.
- Depends on: Local CSV inputs and, in the case of `src/mock_trading_utils.py`, an external `data_paths.py` module that is ignored by `.gitignore`.
- Used by: Manual experiments rather than the documented Docker or inference path.
## Data Flow
- Execution state is run-local and in-memory; there is no long-lived application service or package-wide state container.
- Persistent artifacts are file-based: training writes logs and checkpoints under the user-supplied `workdir`, single-run inference can emit CSVs, and crypto backtests persist candles plus metrics into a SQLite database under `outputs/` by default.
- Configuration is split between CLI flags in `src/*.py`, one reusable config module at `configs/fine_tuning.py`, and environment/platform setup from `Dockerfile` or `scripts/setup_windows.ps1`.
## Key Abstractions
- Purpose: Centralize TimesFM checkpoint and hyperparameter construction for forecasting workflows.
- Examples: `src/run_forecast.py` `build_model()`, `src/main.py` `timesfm.TimesFmCheckpoint(...)`
- Pattern: Direct factory function or direct instantiation around upstream `timesfm` objects.
- Purpose: Override the upstream patched decoder so the loss and prediction path match the repo's finance training assumptions.
- Examples: `src/train.py` `PatchedDecoderFinetuneFinance`
- Pattern: Subclass-and-override of `timesfm.patched_decoder.PatchedDecoderFinetuneModel`.
- Purpose: Convert raw tabular sequences into shapes expected by TimesFM/Pax training and evaluation steps.
- Examples: `src/train.py` `random_masking()`, `prepare_batch_data()`, `reshape_batch()`, `preprocess_csv()`
- Pattern: Functional data-preparation helpers shared across training and evaluation modules.
- Purpose: Keep metrics reusable across rolling evaluation and crypto backtesting paths.
- Examples: `src/evaluate_forecast.py` `mape()`, `smape()`, `directional_accuracy()`; `src/utils.py` `get_accuracy()`, `mse()`
- Pattern: Stateless numeric helper functions operating on `numpy` or JAX arrays.
- Purpose: Isolate the crypto backtest's storage responsibility from the forecasting logic.
- Examples: `src/crypto_minute_backtest.py` `ensure_schema()`, `store_candles()`, `load_candles()`, `save_backtest()`
- Pattern: Plain SQL functions around a `sqlite3.Connection`, with forecasting code passing in already-materialized frames and metrics.
## Entry Points
- Location: `src/main.py`
- Triggers: `python src/main.py --workdir ... --config configs/fine_tuning.py --dataset_path ...`
- Responsibilities: Validate required flags, load config, construct base TimesFM checkpoint, and dispatch to training or checkpoint evaluation.
- Location: `src/run_forecast.py`
- Triggers: `python src/run_forecast.py ...` and the default container start from `Dockerfile`
- Responsibilities: Load one source series, build a forecasting model, execute one forecast, and print or save the result.
- Location: `src/evaluate_forecast.py`
- Triggers: `python src/evaluate_forecast.py ...`
- Responsibilities: Reuse the forecasting helpers to run repeated windows and summarize forecast accuracy.
- Location: `src/crypto_minute_backtest.py`
- Triggers: `python src/crypto_minute_backtest.py ...` or `scripts/run_crypto_backtest.ps1`
- Responsibilities: Fetch Binance candles, maintain the SQLite schema, run batched forecasts, and emit either backtest metrics or a live forecast table.
- Location: `scripts/setup_windows.ps1`
- Triggers: Direct PowerShell execution
- Responsibilities: Enforce Python 3.10, create `.venv`, upgrade `pip`, and install `requirements.inference.txt`.
- Location: `src/mock_trading.py`
- Triggers: `python src/mock_trading.py ...`
- Responsibilities: Load a historical panel, generate long/short positions from TimesFM forecasts, and save per-horizon position CSVs.
## Error Handling
- CLI layers use `argparse` mutual-exclusion groups in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`, and required `absl.flags` in `src/main.py`.
- Data loaders raise `ValueError` for missing columns, empty datasets, too-short series, and invalid evaluation spans in `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`.
- Operational PowerShell scripts wrap external calls in `Invoke-CheckedCommand` and throw immediately on non-zero exit codes.
- Training code in `src/train.py` and `src/evaluation.py` explicitly guards batch/device divisibility, then relies on lower-level JAX/Pax/TimesFM exceptions for deeper runtime failures.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
