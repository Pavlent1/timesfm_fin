# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Framework

**Runner:**
- Not detected. No committed test runner config was found at the repo root or under the approved roots: no `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `conftest.py`, `*.test.*`, or `*.spec.*` files were found next to `README.md`, `src/`, `configs/`, or `scripts/`.
- Current verification is manual and script-driven through the entrypoints documented in `README.md`, `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `scripts/setup_windows.ps1`, and `scripts/run_crypto_backtest.ps1`.

**Assertion Library:**
- Not applicable for committed automation. No `pytest`, `unittest`, or other assertion library usage is present in `src/`, `configs/`, or `scripts/`.

**Run Commands:**
```bash
python src/run_forecast.py --ticker AAPL --period 3y --horizon-len 16
python src/evaluate_forecast.py --tickers AAPL MSFT NVDA --period 5y --horizon-len 16 --test-points 128 --stride 4
python src/crypto_minute_backtest.py --day 2026-04-11 --db-path outputs/crypto_backtest.sqlite --context-len 512 --horizon-len 16 --batch-size 64
.\scripts\run_crypto_backtest.ps1 -Day 2026-04-11
```

## Test File Organization

**Location:**
- No automated test files are committed under `src/`, `configs/`, `scripts/`, or the repository root.
- Manual verification targets the executable modules directly: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `src/main.py`, `scripts/setup_windows.ps1`, and `scripts/run_crypto_backtest.ps1`.

**Naming:**
- Not detected for automated tests.
- The existing manual-verification entrypoints use descriptive production filenames rather than dedicated test wrappers, for example `src/evaluate_forecast.py` and `scripts/run_crypto_backtest.ps1`.

**Structure:**
```text
src/
  run_forecast.py
  evaluate_forecast.py
  crypto_minute_backtest.py
  train.py
  evaluation.py
  utils.py
configs/
  fine_tuning.py
scripts/
  setup_windows.ps1
  run_crypto_backtest.ps1
```

## Test Structure

**Suite Organization:**
```text
No committed automated test suites.

Current verification is manual:
- prepare the environment with `scripts/setup_windows.ps1` or Docker from `README.md`
- run one of the CLI entrypoints in `src/`
- inspect printed tables, optional CSV outputs, or the SQLite database written by `src/crypto_minute_backtest.py`
```

**Patterns:**
- Setup is environment-first rather than fixture-first: `scripts/setup_windows.ps1` creates the virtualenv and installs `requirements.inference.txt`, while `scripts/run_crypto_backtest.ps1` builds and runs Docker around `src/crypto_minute_backtest.py`.
- There is no shared teardown layer. Manual runs clean up implicitly with process exit, Docker `--rm`, or explicit SQLite connection closing in `src/crypto_minute_backtest.py`.
- Assertions are currently human inspection of stdout tables, saved CSVs, and SQLite rows rather than executable expectations.

## Mocking

**Framework:**
- Not detected. No mocking library or monkeypatch pattern is committed in the repository.

**Patterns:**
```python
# No committed mocking examples exist yet.
# Future tests will need to introduce the project's first mock pattern.
```

**What to Mock:**
- Mock network boundaries in first unit tests: `yfinance.download` inside `src/run_forecast.py` and `urllib.request.urlopen` inside `src/crypto_minute_backtest.py`.
- Mock or stub `timesfm.TimesFm.forecast` when testing `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py` so metric and table logic can run deterministically without loading a real checkpoint.
- For integration-style tests around SQLite behavior in `src/crypto_minute_backtest.py`, prefer a temporary database path over mocking SQL execution so schema and persistence paths stay exercised.

**What NOT to Mock:**
- Do not mock pure numeric helpers in `src/evaluate_forecast.py` such as `smape`, `mape`, and `directional_accuracy`.
- Do not mock deterministic utility helpers in `src/crypto_minute_backtest.py` such as `batched`, `annual_returns`, `annualized_volatility`, and `sharpe_ratio`.
- Do not mock simple math helpers in `src/utils.py`; those are better covered with direct input/output assertions.

## Fixtures and Factories

**Test Data:**
```python
# No committed fixtures or factories exist.
# The production code mostly consumes pandas and NumPy objects, so first tests
# should build small inline series/dataframes close to the assertion site.

import numpy as np
import pandas as pd

series = pd.Series([100.0, 101.0, 102.5, 104.0], name="Close")
forecast = np.array([104.5, 105.0], dtype=float)
```

**Location:**
- Not applicable today. There is no `tests/fixtures/`, `tests/factories/`, or helper module dedicated to test data.
- When tests are added, colocated fixture builders near the first test files will match the current small-script structure better than introducing a large shared factory layer immediately.

## Coverage

**Requirements:**
- No coverage target is enforced.
- No automated coverage measurement is configured for `src/`, `configs/`, or `scripts/`.

**Configuration:**
- Not detected. No `.coveragerc`, `pytest.ini`, `tox.ini`, or coverage command is committed beside `README.md`, `src/`, `configs/`, or `scripts/`.
- The current practical coverage model is manual smoke coverage through README workflows, which means regressions in pure helper logic can slip through unnoticed.

**View Coverage:**
```bash
# Not available: no committed coverage command or report configuration.
```

## Test Types

**Unit Tests:**
- Not used today.
- Highest-value first targets are the pure and mostly pure helpers in `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, and `src/utils.py` because they already expose deterministic inputs and outputs.

**Integration Tests:**
- Not automated today.
- The nearest integration workflows are manual runs of `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py`, which exercise Yahoo Finance, Binance, TimesFM, pandas, and SQLite together.

**E2E Tests:**
- Not used.
- The closest end-to-end path is the Docker-backed PowerShell wrapper `scripts/run_crypto_backtest.ps1` plus the command sequences in `README.md`.

## Common Patterns

**Async Testing:**
```python
# Not applicable in the current codebase.
# The production modules in `src/` are synchronous and do not use asyncio.
```

**Error Testing:**
```python
# Not implemented yet.
# First regression tests should assert the ValueError branches in:
# - `src/run_forecast.py` for missing columns, empty data, and too-short context
# - `src/evaluate_forecast.py` for too-short evaluation windows
# - `src/crypto_minute_backtest.py` for empty Binance/SQLite/live-data paths
```

**Snapshot Testing:**
- Not used.
- Current console tables produced by `src/run_forecast.py`, `src/evaluate_forecast.py`, and `src/crypto_minute_backtest.py` are inspected manually rather than snapshot-tested.

---

*Testing analysis: 2026-04-13*
