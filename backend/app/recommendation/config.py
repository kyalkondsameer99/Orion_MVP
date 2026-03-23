"""
Tunable parameters for the rule-based recommendation engine.

Adjust here or construct `RecommendationEngineConfig` in tests without touching core logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationEngineConfig:
    """All magic numbers in one place for readability and A/B tuning."""

    min_reward_risk: float = 2.0
    """Minimum (reward / risk) required to accept a trade."""

    atr_stop_multiplier: float = 1.5
    """Stop distance = max(ATR * this, price * min_stop_fraction)."""

    min_stop_fraction: float = 0.005
    """Floor for stop distance as a fraction of price (0.5%)."""

    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    technical_score_threshold: float = 25.0
    """Absolute composite technical score required to propose LONG/SHORT vs HOLD."""

    rsi_weight: float = 35.0
    ema_trend_weight: float = 25.0
    macd_weight: float = 25.0
    sma_confirm_weight: float = 15.0

    news_block_score: float = 0.35
    """If |news_sentiment_score| exceeds this and conflicts with direction, veto trade."""

    max_position_fraction: float = 0.25
    """Reject if implied notional exceeds this fraction of `account_size`."""

    min_candles: int = 5
    """Minimum bars required to trust swing/ATR context."""
