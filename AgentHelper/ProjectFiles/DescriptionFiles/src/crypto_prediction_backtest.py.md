# `src/crypto_prediction_backtest.py`

This is a standalone backtest entrypoint for the exported
`crypto_prediction_algo_export` BTC microstructure strategy. It fetches
historical Binance 1-minute klines directly, replays the exported
`evaluate_market(...)` logic over rolling windows, converts the strategy's
signal output into a synthetic future close projection, and scores that
projection with the same deviation metrics used by the TimesFM crypto
backtest. It writes a plain-text report plus an optional detail CSV under
`outputs/backtests/`.

Key responsibilities:

- parse a day- or multi-day historical replay window for Binance spot symbols
- fetch enough 1-minute OHLCV history for both the requested range and the
  strategy context lookback
- build synthetic `MarketSnapshot` inputs so the exported strategy can run
  without the rest of the original prediction-market application
- evaluate each rolling decision point against the next N candles
- synthesize per-step predicted closes from the export's composite signal and
  recent microstructure magnitude
- summarize per-step normalized deviation, signed deviation, and average
  overshoot-versus-undershoot percentage magnitudes plus per-output-candle
  direction-guess accuracy in a comparison-friendly report
- optionally export per-window/per-step detail rows to CSV for deeper analysis

Important interactions:

- imports Binance pagination from `src/binance_market_data.py`
- imports the exported strategy types and scoring helpers from
  `crypto_prediction_algo_export/btc_microstructure_model/`
- is launched directly or through `scripts/run_crypto_prediction_backtest.ps1`

Category: strategy replay and report entrypoint.
