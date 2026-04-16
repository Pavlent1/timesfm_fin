# `scripts/run_crypto_prediction_backtest.ps1`

This PowerShell wrapper runs the standalone
`src/crypto_prediction_backtest.py` strategy replay script from a Windows
checkout. It exposes the main tuning knobs for the exported crypto prediction
bundle, forwards them to Python as CLI flags, and prints a short progress line
before execution.

Key responsibilities:

- accept Windows-friendly parameters for symbol, UTC start day, day span,
  history length, future candles, stride, synthetic market prices, and output
  paths
- translate optional parameters like `-WindowMinutes`, `-MaxWindows`,
  `-OutputReport`, and `-OutputCsv` into Python CLI flags only when provided
- invoke `python src/crypto_prediction_backtest.py ...`
- throw if the Python process exits non-zero

Important interactions:

- launches `src/crypto_prediction_backtest.py`
- is intended to mirror the ergonomics of the existing repo-level crypto
  backtest wrappers without requiring Docker or the TimesFM runtime

Category: developer orchestration script.
