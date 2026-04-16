from __future__ import annotations

import math
from typing import Sequence

from .types import BtcMicrostructure, Candle


def compute_rsi(closes: Sequence[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0

    deltas = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    gains = [delta if delta > 0 else 0.0 for delta in deltas[:period]]
    losses = [-delta if delta < 0 else 0.0 for delta in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for delta in deltas[period:]:
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_btc_microstructure(candles: Sequence[Candle]) -> BtcMicrostructure:
    if len(candles) < 20:
        raise ValueError("At least 20 candles are required to compute microstructure.")

    closes = [float(candle.close) for candle in candles]
    highs = [float(candle.high) for candle in candles]
    lows = [float(candle.low) for candle in candles]
    volumes = [float(candle.volume) for candle in candles]

    current_price = closes[-1]
    rsi = compute_rsi(closes, period=14)

    def pct_change(lookback: int) -> float:
        if len(closes) > lookback and closes[-1 - lookback] > 0:
            return (closes[-1] - closes[-1 - lookback]) / closes[-1 - lookback] * 100.0
        return 0.0

    momentum_1m = pct_change(1)
    momentum_5m = pct_change(5)
    momentum_15m = pct_change(15)

    vwap_window = min(30, len(closes))
    typical_prices = [
        (highs[-index] + lows[-index] + closes[-index]) / 3.0
        for index in range(1, vwap_window + 1)
    ]
    vwap_volumes = [volumes[-index] for index in range(1, vwap_window + 1)]
    total_volume = sum(vwap_volumes)
    if total_volume > 0:
        vwap = sum(tp * volume for tp, volume in zip(typical_prices, vwap_volumes)) / total_volume
    else:
        vwap = current_price
    vwap_deviation = (current_price - vwap) / vwap * 100.0 if vwap > 0 else 0.0

    sma5 = sum(closes[-5:]) / 5.0 if len(closes) >= 5 else current_price
    sma15 = sum(closes[-15:]) / 15.0 if len(closes) >= 15 else current_price
    sma_crossover = (sma5 - sma15) / current_price * 100.0 if current_price > 0 else 0.0

    vol_window = min(30, len(closes) - 1)
    returns = [
        (closes[-index] - closes[-index - 1]) / closes[-index - 1]
        for index in range(1, vol_window + 1)
        if closes[-index - 1] > 0
    ]
    if returns:
        mean_return = sum(returns) / len(returns)
        variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
        volatility = math.sqrt(variance) * 100.0
    else:
        volatility = 0.0

    return BtcMicrostructure(
        rsi=rsi,
        momentum_1m=momentum_1m,
        momentum_5m=momentum_5m,
        momentum_15m=momentum_15m,
        vwap=vwap,
        vwap_deviation=vwap_deviation,
        sma_crossover=sma_crossover,
        volatility=volatility,
        price=current_price,
    )
