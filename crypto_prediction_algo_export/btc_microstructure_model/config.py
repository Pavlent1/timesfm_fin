from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    initial_bankroll: float = 10000.0
    kelly_fraction: float = 0.15
    min_edge_threshold: float = 0.02
    max_entry_price: float = 0.55
    max_trade_size: float = 75.0
    min_time_remaining_seconds: int = 60
    max_time_remaining_seconds: int = 1800
    min_convergence_votes: int = 2
    resolved_market_floor: float = 0.02
    resolved_market_ceiling: float = 0.98
    model_probability_floor: float = 0.35
    model_probability_ceiling: float = 0.65
    probability_scale: float = 0.15
    weight_rsi: float = 0.20
    weight_momentum: float = 0.35
    weight_vwap: float = 0.20
    weight_sma: float = 0.15
    weight_market_skew: float = 0.10


DEFAULT_CONFIG = ModelConfig()
