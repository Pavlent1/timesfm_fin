# Model Spec

This document explains the exported BTC 5-minute crypto prediction model exactly enough for another agent to re-run it or port it.

## 1. Scope

This model estimates the probability that the BTC "UP" side of a 5-minute prediction market is mispriced.

It consumes:

- 1-minute BTC candles
- a market snapshot with `up_price` and `down_price`
- optional timing context for filter logic

It produces:

- technical features
- normalized indicator signals
- a composite score
- `model_up_probability`
- trade direction (`up` or `down`)
- raw edge and tradable edge
- confidence
- Kelly-sized suggested position

## 2. Inputs

### Candle Input

Each candle should contain:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

Candles must be sorted oldest to newest.

### Market Input

Each market snapshot should contain:

- `up_price`
- `down_price`
- optional `window_start`
- optional `window_end`
- optional identifiers such as `market_id` or `slug`

## 3. Feature Engineering

All percentage-like feature values below are stored in percentage units, not decimal return units.

Example:

- a `0.10%` move is represented as `0.10`
- a `0.03%` SMA gap is represented as `0.03`

### RSI

RSI uses 14-period Wilder smoothing over close-to-close changes.

If there are fewer than `period + 1` closes, RSI falls back to `50.0`.

Formula:

```text
delta_t = close_t - close_(t-1)
avg_gain_0 = mean(positive deltas over first 14 steps)
avg_loss_0 = mean(abs(negative deltas) over first 14 steps)

avg_gain_t = (avg_gain_(t-1) * 13 + current_gain) / 14
avg_loss_t = (avg_loss_(t-1) * 13 + current_loss) / 14

RS = avg_gain / avg_loss
RSI = 100 - 100 / (1 + RS)
```

### Momentum

Momentum is computed as percent change from the latest close over these lookbacks:

- `1m`
- `5m`
- `15m`

Formula:

```text
momentum_N = (close_now - close_N_bars_ago) / close_N_bars_ago * 100
```

Blended momentum:

```text
mom_blend = momentum_1m * 0.50 + momentum_5m * 0.35 + momentum_15m * 0.15
```

### VWAP

VWAP uses the latest `30` candles, or fewer if less data exists.

Typical price:

```text
typical_price = (high + low + close) / 3
```

VWAP:

```text
VWAP = sum(typical_price_i * volume_i) / sum(volume_i)
```

VWAP deviation:

```text
vwap_deviation = (current_price - VWAP) / VWAP * 100
```

### SMA Crossover

Short SMA: `5` closes  
Long SMA: `15` closes

Formula:

```text
sma_crossover = (SMA_5 - SMA_15) / current_price * 100
```

### Volatility

Volatility is the standard deviation of 1-minute decimal returns over the last `30` return observations, then scaled into percent units.

Formula:

```text
return_t = (close_t - close_(t-1)) / close_(t-1)
volatility = stdev(return_t) * 100
```

## 4. Indicator Signal Mapping

Each indicator becomes a bounded signal in `[-1, +1]`.

Positive means bullish for `UP`.  
Negative means bearish for `UP` / bullish for `DOWN`.

### RSI Signal

Piecewise mapping:

```text
if RSI < 30:
    rsi_signal = 0.5 + (30 - RSI) / 30
elif RSI > 70:
    rsi_signal = -0.5 - (RSI - 70) / 30
elif RSI < 45:
    rsi_signal = (45 - RSI) / 30
elif RSI > 55:
    rsi_signal = -(RSI - 55) / 30
else:
    rsi_signal = 0

rsi_signal = clip(rsi_signal, -1, 1)
```

Interpretation:

- oversold BTC means mean-reversion bias toward `UP`
- overbought BTC means mean-reversion bias toward `DOWN`

### Momentum Signal

```text
momentum_signal = clip(mom_blend / 0.10, -1, 1)
```

Because momentum values are already in percentage units, `0.10` means `0.10%`.

### VWAP Signal

```text
vwap_signal = clip(vwap_deviation / 0.05, -1, 1)
```

### SMA Signal

```text
sma_signal = clip(sma_crossover / 0.03, -1, 1)
```

### Market Skew Signal

This is contrarian. If the market already leans heavily toward `UP`, the model fades it.

```text
market_skew = up_price - 0.50
skew_signal = clip(-market_skew * 4, -1, 1)
```

## 5. Convergence Filter

The model counts directional votes using only the first four technical signals:

- RSI
- Momentum
- VWAP
- SMA

Vote rules:

```text
UP vote if signal > 0.05
DOWN vote if signal < -0.05
```

Convergence passes if:

```text
up_votes >= 2 or down_votes >= 2
```

## 6. Composite Model

Default weights:

```text
RSI         = 0.20
Momentum    = 0.35
VWAP        = 0.20
SMA         = 0.15
MarketSkew  = 0.10
```

Composite:

```text
composite =
    rsi_signal * 0.20 +
    momentum_signal * 0.35 +
    vwap_signal * 0.20 +
    sma_signal * 0.15 +
    skew_signal * 0.10
```

The composite is then converted to `UP` probability:

```text
model_up_probability = clip(0.50 + composite * 0.15, 0.35, 0.65)
```

So the model never emits probabilities below `35%` or above `65%`.

## 7. Edge Logic

Market-implied `UP` probability is `up_price`.

Raw signed edge relative to the `UP` side:

```text
signed_up_edge = model_up_probability - market_up_probability
```

Direction choice:

```text
up_edge = model_up_probability - market_up_probability
down_edge = (1 - model_up_probability) - (1 - market_up_probability)
```

Since `down_edge = market_up_probability - model_up_probability`, the chosen direction is:

- `up` if `signed_up_edge >= 0`
- `down` if `signed_up_edge < 0`

Magnitude:

```text
raw_edge = abs(signed_up_edge)
```

## 8. Filters

The exported model keeps the raw edge visible, but only exposes `tradable_edge` when all filters pass.

### Filter A: Resolved-Market Guard

Skip market if:

```text
up_price < 0.02 or up_price > 0.98
```

### Filter B: Cheap-Side Entry

Entry price:

- if direction is `up`, entry price is `up_price`
- if direction is `down`, entry price is `down_price`

Rule:

```text
entry_price <= 0.55
```

### Filter C: Time Window

If `window_end` and `now` are provided:

```text
time_remaining_seconds = window_end - now
```

Rule:

```text
60 <= time_remaining_seconds <= 1800
```

### Filter D: Convergence

Requires the convergence rule from section 5.

### Threshold

After filters pass, the trade still needs:

```text
tradable_edge >= 0.02
```

`actionable = passes_filters and tradable_edge >= min_edge_threshold`

## 9. Confidence

Confidence is not a calibrated probability. It is a heuristic score.

Convergence strength:

```text
convergence_strength = max(up_votes, down_votes) / 4
```

Volatility factor:

```text
if volatility > 0:
    vol_factor = min(1.0, volatility / 0.05)
else:
    vol_factor = 0.5
```

Confidence formula:

```text
confidence = min(0.8, 0.3 + convergence_strength * 0.3 + abs(composite) * 0.2) * vol_factor
```

## 10. Position Sizing

The model uses fractional Kelly on the chosen side.

For `up`:

```text
win_prob = model_up_probability
price = market_up_probability
```

For `down`:

```text
win_prob = 1 - model_up_probability
price = 1 - market_up_probability
```

Odds:

```text
odds = (1 - price) / price
lose_prob = 1 - win_prob
kelly = (win_prob * odds - lose_prob) / odds
```

Fractional Kelly:

```text
kelly = kelly * 0.15
kelly = min(kelly, 0.05)
kelly = max(kelly, 0.0)
position_size = min(kelly * bankroll, 75.0)
```

Default bankroll in the export: `10000.0`

## 11. Calibration Metrics

The export includes helpers for backtest evaluation.

### Brier Score

For actual `UP` outcome in `{0, 1}`:

```text
brier = mean((predicted_up_probability - actual_up_outcome)^2)
```

### Direction Accuracy

```text
predicted_direction = "up" if predicted_up_probability >= market_up_probability else "down"
correct if predicted_direction matches actual direction
```

### Average Predicted Edge

Mean of model edge magnitudes over settled predictions.

### Average Actual Edge

Equivalent to the current app logic:

- `+edge` when the prediction direction was correct
- `-edge` when it was wrong

## 12. Important Limitations

- This is a short-horizon heuristic model, not a statistically estimated probability model.
- Probability outputs are intentionally capped to `35%-65%`.
- Confidence is only a ranking heuristic.
- No slippage, fees, or fill model is included in this export.
- For fair comparison with other models, evaluate all models on the same decision timestamps and market snapshots.
