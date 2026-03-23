"""
Deterministic recommendation logic.

Steps:
1. Build a composite technical score from RSI / EMA / MACD / SMA.
2. Apply news veto / soft filters.
3. Propose LONG or SHORT with ATR-based (or %-floor) stops.
4. Enforce minimum reward:risk (`min_reward_risk`, default 2.0).
5. Validate dollar risk vs `account_size` * `risk_percent` and position cap.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from app.recommendation.config import RecommendationEngineConfig
from app.schemas.recommendation_engine import (
    RecommendationRequest,
    RecommendationResponse,
)

Bias = Literal["long", "short", "none"]


def run_recommendation(
    req: RecommendationRequest,
    config: RecommendationEngineConfig | None = None,
) -> RecommendationResponse:
    cfg = config or RecommendationEngineConfig()
    sym = req.symbol.strip().upper()

    if len(req.candles) < cfg.min_candles:
        return _hold(
            sym,
            f"Insufficient history: need at least {cfg.min_candles} candles.",
            req.news.summary,
            technical_summary="Not enough bars to score the setup.",
            confidence=0.15,
        )

    last = req.candles[-1]
    close = float(last.close)
    high = float(last.high)
    low = float(last.low)

    ind = req.indicators
    atr = float(ind.atr) if ind.atr is not None else None

    tech_score, tech_summary = _technical_score_and_summary(close, ind, cfg)
    news_summary_short = (req.news.summary or "")[:400]

    bias: Bias = "none"
    if tech_score >= cfg.technical_score_threshold:
        bias = "long"
    elif tech_score <= -cfg.technical_score_threshold:
        bias = "short"

    if bias == "none":
        return _hold(
            sym,
            "Technical composite did not clear the directional threshold.",
            news_summary_short,
            technical_summary=tech_summary,
            confidence=_confidence_from_score(abs(tech_score), cfg.technical_score_threshold),
        )

    if _news_vetoes(bias, float(req.news.sentiment_score), cfg):
        return _hold(
            sym,
            "News sentiment conflicts strongly with the technical bias — standing aside.",
            news_summary_short,
            technical_summary=tech_summary,
            confidence=0.25,
        )

    stop_dist = _stop_distance(close, high, low, atr, cfg)
    if stop_dist <= 0 or stop_dist >= close:
        return _hold(
            sym,
            "Invalid stop distance after ATR / floor sizing.",
            news_summary_short,
            technical_summary=tech_summary,
            confidence=0.2,
        )

    rr = cfg.min_reward_risk
    if bias == "long":
        entry = close
        stop = entry - stop_dist
        tp = entry + rr * stop_dist
        action: Literal["BUY", "SELL", "HOLD"] = "BUY"
        direction: Literal["LONG", "SHORT", "NONE"] = "LONG"
        risk_per_share = entry - stop
        reward_per_share = tp - entry
    else:
        entry = close
        stop = entry + stop_dist
        tp = entry - rr * stop_dist
        action = "SELL"
        direction = "SHORT"
        risk_per_share = stop - entry
        reward_per_share = entry - tp

    if risk_per_share <= 0:
        return _hold(sym, "Non-positive per-share risk.", news_summary_short, technical_summary=tech_summary)

    realized_rr = reward_per_share / risk_per_share
    if realized_rr + 1e-9 < cfg.min_reward_risk:
        return _hold(
            sym,
            f"Reward:risk {realized_rr:.2f} below minimum {cfg.min_reward_risk:.2f}.",
            news_summary_short,
            technical_summary=tech_summary,
        )

    acct = float(req.account_size)
    risk_budget = acct * (float(req.risk_percent) / 100.0)
    shares = risk_budget / risk_per_share
    notional = shares * entry

    if notional > acct * cfg.max_position_fraction:
        return _hold(
            sym,
            f"Implied notional {notional:.2f} exceeds {cfg.max_position_fraction:.0%} of account cap.",
            news_summary_short,
            technical_summary=tech_summary,
            confidence=0.3,
        )

    if shares <= 0 or notional <= 0:
        return _hold(sym, "Position size collapsed after risk checks.", news_summary_short, technical_summary=tech_summary)

    conf = _finalize_confidence(abs(tech_score), cfg, req.news.sentiment, bias)

    reason = (
        f"{sym}: {direction} setup — technical score {tech_score:+.1f} vs ±{cfg.technical_score_threshold:.1f}. "
        f"Stop distance {stop_dist:.4f} (ATR/floor). RR target {cfg.min_reward_risk:.1f}:1 achieved at {realized_rr:.2f}:1. "
        f"Risk budget ${risk_budget:,.2f} vs per-share risk ${risk_per_share:.4f}."
    )

    return RecommendationResponse(
        action=action,
        direction=direction,
        entry_price=entry,
        stop_loss=stop,
        take_profit=tp,
        confidence=conf,
        technical_summary=tech_summary,
        news_summary=news_summary_short,
        reason_summary=reason,
        passed_risk_checks=True,
        reward_risk_ratio=float(realized_rr),
    )


def _technical_score_and_summary(
    close: float,
    ind,
    cfg: RecommendationEngineConfig,
) -> tuple[float, str]:
    parts: list[str] = []
    score = 0.0

    if ind.rsi is not None:
        rsi = float(ind.rsi)
        if rsi <= cfg.rsi_oversold:
            score += cfg.rsi_weight
            parts.append(f"RSI {rsi:.1f} (oversold → long bias)")
        elif rsi >= cfg.rsi_overbought:
            score -= cfg.rsi_weight
            parts.append(f"RSI {rsi:.1f} (overbought → short bias)")
        else:
            parts.append(f"RSI {rsi:.1f} (neutral)")

    if ind.ema is not None:
        ema = float(ind.ema)
        if close > ema:
            score += cfg.ema_trend_weight
            parts.append("Price above EMA (bullish)")
        elif close < ema:
            score -= cfg.ema_trend_weight
            parts.append("Price below EMA (bearish)")
        else:
            parts.append("Price near EMA")

    if ind.macd_histogram is not None:
        mh = float(ind.macd_histogram)
        if mh > 0:
            score += cfg.macd_weight
            parts.append("MACD histogram > 0")
        elif mh < 0:
            score -= cfg.macd_weight
            parts.append("MACD histogram < 0")
        else:
            parts.append("MACD histogram flat")

    if ind.sma is not None and ind.ema is not None:
        sma = float(ind.sma)
        ema = float(ind.ema)
        if ema > sma:
            score += cfg.sma_confirm_weight
            parts.append("EMA above SMA (bullish stack)")
        elif ema < sma:
            score -= cfg.sma_confirm_weight
            parts.append("EMA below SMA (bearish stack)")

    if not parts:
        parts.append("Limited indicators supplied — weak conviction")

    return score, "; ".join(parts)


def _news_vetoes(bias: Bias, news_score: float, cfg: RecommendationEngineConfig) -> bool:
    if abs(news_score) < cfg.news_block_score:
        return False
    if bias == "long" and news_score <= -cfg.news_block_score:
        return True
    if bias == "short" and news_score >= cfg.news_block_score:
        return True
    return False


def _stop_distance(
    close: float,
    high: float,
    low: float,
    atr: float | None,
    cfg: RecommendationEngineConfig,
) -> float:
    floor = close * cfg.min_stop_fraction
    if atr is not None and atr > 0:
        return max(atr * cfg.atr_stop_multiplier, floor)
    # Fallback: recent bar range clamp
    rng = max(high - low, close * cfg.min_stop_fraction)
    return max(rng, floor)


def _confidence_from_score(mag: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.5
    return max(0.1, min(0.95, 0.35 + 0.45 * min(1.0, mag / threshold)))


def _finalize_confidence(
    mag: float,
    cfg: RecommendationEngineConfig,
    sentiment: str,
    bias: Bias,
) -> float:
    base = _confidence_from_score(mag, cfg.technical_score_threshold)
    if sentiment == "neutral":
        return max(0.1, base - 0.05)
    if bias == "long" and sentiment == "positive":
        return min(0.95, base + 0.08)
    if bias == "short" and sentiment == "negative":
        return min(0.95, base + 0.08)
    if bias == "long" and sentiment == "negative":
        return max(0.15, base - 0.12)
    if bias == "short" and sentiment == "positive":
        return max(0.15, base - 0.12)
    return base


def _hold(
    symbol: str,
    reason: str,
    news_summary: str,
    *,
    technical_summary: str,
    confidence: float,
) -> RecommendationResponse:
    return RecommendationResponse(
        action="HOLD",
        direction="NONE",
        entry_price=None,
        stop_loss=None,
        take_profit=None,
        confidence=confidence,
        technical_summary=technical_summary,
        news_summary=news_summary,
        reason_summary=f"{symbol}: HOLD — {reason}",
        passed_risk_checks=False,
        reward_risk_ratio=None,
    )
