# Backtest Guide

This guide explains how to use the export bundle on a historical data chunk.

## 1. Data You Need

For each decision timestamp:

- the most recent 1-minute BTC candles, oldest to newest
- the market snapshot at that same timestamp:
  - `up_price`
  - `down_price`
  - optional `window_end`
- the realized market outcome later:
  - `1.0` if `UP` won
  - `0.0` if `DOWN` won

## 2. Replay Pattern

For each backtest row:

1. build the candle slice ending at the decision timestamp
2. build a `MarketSnapshot`
3. call `evaluate_market(...)`
4. store the full result, not just actionable trades
5. once the market resolves, create a `SettledPrediction`
6. summarize with `summarize_calibration(...)`

## 3. Recommended Evaluation Policy

Keep two result sets:

- all valid evaluations
- actionable evaluations only

This lets you compare:

- raw model forecasting quality
- tradable performance after filters

## 4. Minimal Replay Example

```python
from datetime import timezone

from btc_microstructure_model import (
    Candle,
    MarketSnapshot,
    SettledPrediction,
    evaluate_market,
    summarize_calibration,
)

settled = []

for row in dataset:
    candles = [
        Candle(
            timestamp=c.timestamp.astimezone(timezone.utc),
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
        )
        for c in row.candles
    ]

    market = MarketSnapshot(
        market_id=row.market_id,
        slug=row.slug,
        up_price=row.up_price,
        down_price=row.down_price,
        window_end=row.window_end,
        volume=row.market_volume,
    )

    signal = evaluate_market(market=market, candles=candles, now=row.timestamp)
    if not signal.valid:
        continue

    settled.append(
        SettledPrediction(
            predicted_up_probability=signal.model_up_probability,
            market_up_probability=signal.market_up_probability,
            edge=signal.tradable_edge,
            direction=signal.direction,
            actual_up_outcome=row.actual_up_outcome,
        )
    )

summary = summarize_calibration(settled)
print(summary)
```

## 5. Compare Against Other Models

When comparing this exported model against another model:

- use identical timestamps
- use identical candle windows
- use identical market prices
- define the same execution eligibility rules, or compare both:
  - forecast quality only
  - forecast quality plus execution rules

Useful comparison metrics:

- Brier score
- direction accuracy
- average predicted edge
- signed realized edge
- trade count
- hit rate on actionable trades

## 6. Practical Notes

- Use at least `60` candles for stable feature values.
- If you do not have `window_end`, the time filter is skipped.
- If you want pure forecast comparison without entry/time filters, compare on `raw_edge` and ignore `actionable`.
- If you want behavior closest to the live bot, use `tradable_edge` and `actionable`.
