# `src/mock_trading.py`

This script generates position CSVs for mock trading experiments from a TimesFM checkpoint. It loads a market-specific dataset through `src/mock_trading_utils.py`, walks forward over post-2023 dates, runs forecasts for one or more horizon lengths, converts the predicted start-to-end move into long or short positions, and saves one positions file per horizon.

Important behaviors:

- uses `absl.flags` rather than `argparse`
- can load either a supplied checkpoint or the original model checkpoint path flow
- optionally applies `plus_one` and log transforms before forecasting and reverses them afterward
- writes outputs under a per-checkpoint folder inside the requested work directory

Category: experiment script.
