# `scripts/run_crypto_backtest.ps1`

This PowerShell wrapper runs `src/crypto_minute_backtest.py` inside Docker from a Windows checkout. It optionally builds the Docker image, mounts the repository into `/workspace`, translates CLI parameters into the Python entrypoint flags, and switches to `--gpus all` automatically when `-Backend gpu` is selected.

The script is the Windows-facing launcher for the Binance minute backtest and live forecast flow. Its main external dependency is Docker; its main side effect is invoking the containerized Python script against the mounted repo, which then writes SQLite and optional CSV outputs under the mounted workspace.

Category: developer orchestration script.
