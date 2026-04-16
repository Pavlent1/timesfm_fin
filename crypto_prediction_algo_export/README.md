# Crypto Prediction Algo Export

This folder is an export-ready bundle of the BTC 5-minute microstructure model extracted from this repo.

It is intended for:

- replaying the model on historical candle data
- comparing this model against other models on the same backtest dataset
- giving another agent a self-contained package plus documentation

This export does not include the full app, API clients, database, scheduler, or UI. It keeps only the reusable analysis logic.

## Folder Layout

```text
crypto_prediction_algo_export/
|-- README.md
|-- docs/
|   |-- BACKTEST_GUIDE.md
|   |-- MODEL_SPEC.md
|   `-- SOURCE_MAP.md
`-- btc_microstructure_model/
    |-- __init__.py
    |-- calibration.py
    |-- config.py
    |-- indicators.py
    |-- signal_model.py
    `-- types.py
```

## What The Model Needs

For each evaluation timestamp:

- a rolling window of 1-minute BTC candles, oldest to newest
- the prediction-market snapshot for the same decision point

Minimum practical candle history: `60` one-minute candles.  
Hard minimum supported by the formulas: `20` candles.

## Main Entry Points

- `btc_microstructure_model.compute_btc_microstructure(candles)`
- `btc_microstructure_model.evaluate_market(market, candles, now=...)`
- `btc_microstructure_model.summarize_calibration(predictions)`

## Quick Example

```python
from datetime import datetime, timezone

from btc_microstructure_model import Candle, MarketSnapshot, evaluate_market

candles = [
    Candle(timestamp=datetime.now(timezone.utc), open=100, high=101, low=99, close=100.5, volume=12),
    # ... oldest -> newest, ideally 60 rows
]

market = MarketSnapshot(
    market_id="123",
    slug="btc-updown-5m-0000000000",
    up_price=0.47,
    down_price=0.53,
)

signal = evaluate_market(market=market, candles=candles, now=datetime.now(timezone.utc))
print(signal.actionable, signal.direction, signal.model_up_probability, signal.tradable_edge)
```

## Notes

- All formulas match the current repo logic, including thresholds and weight defaults.
- This bundle is pure Python standard library only.
- The detailed math is documented in [docs/MODEL_SPEC.md](docs/MODEL_SPEC.md).
