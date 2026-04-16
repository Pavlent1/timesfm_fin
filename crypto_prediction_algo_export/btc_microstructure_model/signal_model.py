from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from .config import DEFAULT_CONFIG, ModelConfig
from .indicators import compute_btc_microstructure
from .types import Candle, IndicatorSignals, MarketSnapshot, SignalEvaluation


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def calculate_edge(model_prob: float, market_price: float) -> tuple[float, str]:
    up_edge = model_prob - market_price
    down_edge = (1.0 - model_prob) - (1.0 - market_price)
    if up_edge >= down_edge:
        return up_edge, "up"
    return down_edge, "down"


def calculate_kelly_size(
    edge: float,
    probability: float,
    market_price: float,
    direction: str,
    bankroll: float,
    config: ModelConfig = DEFAULT_CONFIG,
) -> tuple[float, float]:
    del edge

    if direction == "up":
        win_prob = probability
        price = market_price
    else:
        win_prob = 1.0 - probability
        price = 1.0 - market_price

    if price <= 0.0 or price >= 1.0:
        return 0.0, 0.0

    odds = (1.0 - price) / price
    lose_prob = 1.0 - win_prob
    kelly = (win_prob * odds - lose_prob) / odds
    kelly *= config.kelly_fraction
    kelly = min(kelly, 0.05)
    kelly = max(kelly, 0.0)

    size = min(kelly * bankroll, config.max_trade_size)
    return kelly, size


def _normalize_timestamp(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def evaluate_market(
    market: MarketSnapshot,
    candles: Sequence[Candle],
    now: Optional[datetime] = None,
    config: ModelConfig = DEFAULT_CONFIG,
) -> SignalEvaluation:
    try:
        micro = compute_btc_microstructure(candles)
    except ValueError as error:
        return SignalEvaluation(
            valid=False,
            actionable=False,
            direction="up",
            model_up_probability=0.5,
            market_up_probability=market.up_price,
            signed_up_edge=0.0,
            raw_edge=0.0,
            tradable_edge=0.0,
            entry_price=market.up_price,
            confidence=0.0,
            kelly_fraction=0.0,
            suggested_size=0.0,
            passes_filters=False,
            passes_threshold=False,
            time_remaining_seconds=None,
            filter_reasons=(str(error),),
            reasoning=str(error),
        )

    market_up_prob = market.up_price
    if (
        market_up_prob < config.resolved_market_floor
        or market_up_prob > config.resolved_market_ceiling
    ):
        reason = "market appears effectively resolved"
        return SignalEvaluation(
            valid=False,
            actionable=False,
            direction="up",
            model_up_probability=0.5,
            market_up_probability=market_up_prob,
            signed_up_edge=0.0,
            raw_edge=0.0,
            tradable_edge=0.0,
            entry_price=market.up_price,
            confidence=0.0,
            kelly_fraction=0.0,
            suggested_size=0.0,
            passes_filters=False,
            passes_threshold=False,
            time_remaining_seconds=None,
            filter_reasons=(reason,),
            microstructure=micro,
            reasoning=reason,
        )

    if micro.rsi < 30.0:
        rsi_signal = 0.5 + (30.0 - micro.rsi) / 30.0
    elif micro.rsi > 70.0:
        rsi_signal = -0.5 - (micro.rsi - 70.0) / 30.0
    elif micro.rsi < 45.0:
        rsi_signal = (45.0 - micro.rsi) / 30.0
    elif micro.rsi > 55.0:
        rsi_signal = -(micro.rsi - 55.0) / 30.0
    else:
        rsi_signal = 0.0
    rsi_signal = _clip(rsi_signal, -1.0, 1.0)

    momentum_blend = (
        micro.momentum_1m * 0.50
        + micro.momentum_5m * 0.35
        + micro.momentum_15m * 0.15
    )
    momentum_signal = _clip(momentum_blend / 0.10, -1.0, 1.0)
    vwap_signal = _clip(micro.vwap_deviation / 0.05, -1.0, 1.0)
    sma_signal = _clip(micro.sma_crossover / 0.03, -1.0, 1.0)

    market_skew = market_up_prob - 0.50
    skew_signal = _clip(-market_skew * 4.0, -1.0, 1.0)

    indicator_signs = [rsi_signal, momentum_signal, vwap_signal, sma_signal]
    up_votes = sum(1 for signal in indicator_signs if signal > 0.05)
    down_votes = sum(1 for signal in indicator_signs if signal < -0.05)
    has_convergence = (
        up_votes >= config.min_convergence_votes
        or down_votes >= config.min_convergence_votes
    )

    composite = (
        rsi_signal * config.weight_rsi
        + momentum_signal * config.weight_momentum
        + vwap_signal * config.weight_vwap
        + sma_signal * config.weight_sma
        + skew_signal * config.weight_market_skew
    )
    model_up_prob = _clip(
        0.50 + composite * config.probability_scale,
        config.model_probability_floor,
        config.model_probability_ceiling,
    )

    edge_value, direction = calculate_edge(model_up_prob, market_up_prob)
    signed_up_edge = model_up_prob - market_up_prob
    raw_edge = abs(edge_value)

    entry_price = market.up_price if direction == "up" else market.down_price

    normalized_now = _normalize_timestamp(now)
    normalized_end = _normalize_timestamp(market.window_end)
    time_remaining_seconds: Optional[float] = None
    time_ok = True
    if normalized_now is not None and normalized_end is not None:
        time_remaining_seconds = (normalized_end - normalized_now).total_seconds()
        time_ok = (
            config.min_time_remaining_seconds
            <= time_remaining_seconds
            <= config.max_time_remaining_seconds
        )

    filter_reasons = []
    if not has_convergence:
        filter_reasons.append(
            f"convergence {max(up_votes, down_votes)}/4 < {config.min_convergence_votes}"
        )
    if entry_price > config.max_entry_price:
        filter_reasons.append(
            f"entry {entry_price:.0%} > {config.max_entry_price:.0%}"
        )
    if not time_ok and time_remaining_seconds is not None:
        filter_reasons.append(
            "time "
            f"{time_remaining_seconds:.0f}s not in "
            f"[{config.min_time_remaining_seconds},{config.max_time_remaining_seconds}]"
        )

    passes_filters = has_convergence and entry_price <= config.max_entry_price and time_ok
    tradable_edge = raw_edge if passes_filters else 0.0
    passes_threshold = tradable_edge >= config.min_edge_threshold
    actionable = passes_filters and passes_threshold

    if micro.volatility > 0.0:
        vol_factor = min(1.0, micro.volatility / 0.05)
    else:
        vol_factor = 0.5
    convergence_strength = max(up_votes, down_votes) / 4.0
    confidence = min(0.8, 0.3 + convergence_strength * 0.3 + abs(composite) * 0.2) * vol_factor

    kelly_fraction, suggested_size = calculate_kelly_size(
        edge=tradable_edge,
        probability=model_up_prob,
        market_price=market_up_prob,
        direction=direction,
        bankroll=config.initial_bankroll,
        config=config,
    )

    indicators = IndicatorSignals(
        rsi_signal=rsi_signal,
        momentum_signal=momentum_signal,
        vwap_signal=vwap_signal,
        sma_signal=sma_signal,
        skew_signal=skew_signal,
        composite=composite,
        up_votes=up_votes,
        down_votes=down_votes,
    )

    status = "ACTIONABLE" if actionable else "FILTERED"
    reasoning = (
        f"[{status}] "
        f"BTC {micro.price:.2f} | "
        f"RSI:{micro.rsi:.1f} Mom1m:{micro.momentum_1m:+.3f}% "
        f"Mom5m:{micro.momentum_5m:+.3f}% VWAP:{micro.vwap_deviation:+.3f}% "
        f"SMA:{micro.sma_crossover:+.4f}% Vol:{micro.volatility:.4f}% | "
        f"Composite:{composite:+.3f} -> Model UP:{model_up_prob:.1%} vs Mkt:{market_up_prob:.1%} | "
        f"Raw edge:{raw_edge:.1%} Tradable edge:{tradable_edge:.1%} | "
        f"Direction:{direction.upper()} @ {entry_price:.0%}"
    )
    if filter_reasons:
        reasoning += " | Filters: " + ", ".join(filter_reasons)

    return SignalEvaluation(
        valid=True,
        actionable=actionable,
        direction=direction,
        model_up_probability=model_up_prob,
        market_up_probability=market_up_prob,
        signed_up_edge=signed_up_edge,
        raw_edge=raw_edge,
        tradable_edge=tradable_edge,
        entry_price=entry_price,
        confidence=confidence,
        kelly_fraction=kelly_fraction,
        suggested_size=suggested_size,
        passes_filters=passes_filters,
        passes_threshold=passes_threshold,
        time_remaining_seconds=time_remaining_seconds,
        filter_reasons=tuple(filter_reasons),
        microstructure=micro,
        indicators=indicators,
        reasoning=reasoning,
    )
