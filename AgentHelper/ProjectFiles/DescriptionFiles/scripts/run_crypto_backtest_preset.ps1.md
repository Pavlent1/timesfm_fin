# `scripts/run_crypto_backtest_preset.ps1`

This preset PowerShell launcher is the easiest operator-facing entrypoint for
repeated crypto backtest runs from a Windows checkout. It keeps the main run
settings as editable variables at the top of the file, then forwards them into
`scripts/run_crypto_backtest.ps1`.

Key responsibilities:

- expose the most common backtest parameters as top-of-file variables
- default to no image rebuilds for repeated runs against an already-built Docker image
- default to GPU execution, `horizon_len=5`, and `stride=5`
- support single-day or multi-day historical runs through `StartDay` and `Days`
- forward PostgreSQL and Hugging Face cache settings into the shared Docker wrapper

Important interactions:

- delegates the real Docker invocation to `scripts/run_crypto_backtest.ps1`
- relies on Docker, the existing `timesfm-fin` image, and the Phase 1 PostgreSQL dataset

Category: operator preset runner.
