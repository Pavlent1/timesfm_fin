# `scripts/run_crypto_backtest.ps1`

This PowerShell wrapper runs `src/crypto_minute_backtest.py` inside Docker from
a Windows checkout. It optionally builds the Docker image, mounts the
repository into `/workspace`, translates the main tuning parameters into the
Python entrypoint flags, injects PostgreSQL connection settings as container
environment variables, defaults the runtime to CPU for the documented Windows
path, and switches to `--gpus all` automatically when `-Backend gpu` is
selected.

The script is the Windows-facing launcher for the Binance minute backtest and
live forecast flow. Its main external dependency is Docker; its main side
effect is invoking the containerized Python script against the mounted repo
while wiring the container to the host PostgreSQL service through
`host.docker.internal` and `--add-host=host.docker.internal:host-gateway`.

Category: developer orchestration script.
