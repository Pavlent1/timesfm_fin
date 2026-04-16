from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketSnapshot:
    market_id: str = ""
    slug: str = ""
    up_price: float = 0.5
    down_price: float = 0.5
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    volume: float = 0.0


@dataclass(frozen=True)
class BtcMicrostructure:
    rsi: float = 50.0
    momentum_1m: float = 0.0
    momentum_5m: float = 0.0
    momentum_15m: float = 0.0
    vwap: float = 0.0
    vwap_deviation: float = 0.0
    sma_crossover: float = 0.0
    volatility: float = 0.0
    price: float = 0.0


@dataclass(frozen=True)
class IndicatorSignals:
    rsi_signal: float
    momentum_signal: float
    vwap_signal: float
    sma_signal: float
    skew_signal: float
    composite: float
    up_votes: int
    down_votes: int


@dataclass(frozen=True)
class SignalEvaluation:
    valid: bool
    actionable: bool
    direction: str
    model_up_probability: float
    market_up_probability: float
    signed_up_edge: float
    raw_edge: float
    tradable_edge: float
    entry_price: float
    confidence: float
    kelly_fraction: float
    suggested_size: float
    passes_filters: bool
    passes_threshold: bool
    time_remaining_seconds: Optional[float]
    filter_reasons: Tuple[str, ...] = field(default_factory=tuple)
    microstructure: Optional[BtcMicrostructure] = None
    indicators: Optional[IndicatorSignals] = None
    reasoning: str = ""


@dataclass(frozen=True)
class SettledPrediction:
    predicted_up_probability: float
    market_up_probability: float
    edge: float
    direction: str
    actual_up_outcome: float


@dataclass(frozen=True)
class CalibrationBucket:
    bucket: str
    predicted_avg: float
    actual_rate: float
    count: int


@dataclass(frozen=True)
class CalibrationSummary:
    total_predictions: int
    total_with_outcome: int
    accuracy: float
    avg_predicted_edge: float
    avg_actual_edge: float
    brier_score: float
