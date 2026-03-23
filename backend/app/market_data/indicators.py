"""
Pure NumPy technical indicators — no I/O, easy to unit test.

Conventions:
- Inputs are 1-D `float` arrays (same length).
- Outputs align with inputs; warm-up bars are `nan` where undefined.
- RSI / ATR use Wilder RMA smoothing where applicable.
"""

from __future__ import annotations

import numpy as np


def _as_float(a: np.ndarray | list[float]) -> np.ndarray:
    return np.asarray(a, dtype=float)


def sma(values: np.ndarray | list[float], period: int) -> np.ndarray:
    """Simple moving average."""
    v = _as_float(values)
    n = len(v)
    out = np.full(n, np.nan)
    if period <= 0 or n < period:
        return out
    c = np.cumsum(np.insert(v, 0, 0.0))
    out[period - 1 :] = (c[period:] - c[:-period]) / period
    return out


def ema(values: np.ndarray | list[float], period: int) -> np.ndarray:
    """Exponential moving average (EMA) with seed = first price."""
    v = _as_float(values)
    n = len(v)
    out = np.full(n, np.nan)
    if period <= 0 or n == 0:
        return out
    alpha = 2.0 / (period + 1.0)
    out[0] = v[0]
    for i in range(1, n):
        out[i] = alpha * v[i] + (1.0 - alpha) * out[i - 1]
    return out


def rma(values: np.ndarray | list[float], period: int) -> np.ndarray:
    """Wilder smoothed moving average (RMA)."""
    v = _as_float(values)
    n = len(v)
    out = np.full(n, np.nan)
    if period <= 0 or n < period:
        return out
    out[period - 1] = float(np.mean(v[:period]))
    for i in range(period, n):
        out[i] = (out[i - 1] * (period - 1) + v[i]) / period
    return out


def rsi(close: np.ndarray | list[float], period: int = 14) -> np.ndarray:
    """Relative Strength Index (Wilder)."""
    c = _as_float(close)
    n = len(c)
    out = np.full(n, np.nan)
    if period <= 0 or n < period:
        return out

    changes = np.zeros_like(c)
    if n > 1:
        changes[1:] = c[1:] - c[:-1]
    gains = np.where(changes > 0, changes, 0.0)
    losses = np.where(changes < 0, -changes, 0.0)

    avg_gain = rma(gains, period)
    avg_loss = rma(losses, period)

    invalid = np.isnan(avg_gain) | np.isnan(avg_loss)
    rs = np.divide(
        avg_gain,
        avg_loss,
        out=np.zeros_like(avg_gain, dtype=float),
        where=(avg_loss != 0) & ~np.isnan(avg_loss),
    )
    out = 100.0 - (100.0 / (1.0 + rs))

    # Edge cases: flat market (only where averages are defined).
    out = np.where(invalid, np.nan, out)
    out = np.where(~invalid & (avg_loss == 0) & (avg_gain == 0), 50.0, out)
    out = np.where(~invalid & (avg_loss == 0) & (avg_gain > 0), 100.0, out)
    return out


def true_range(high: np.ndarray | list[float], low: np.ndarray | list[float], close: np.ndarray | list[float]) -> np.ndarray:
    """True range series."""
    h, l, c = map(_as_float, (high, low, close))
    prev_c = np.roll(c, 1)
    prev_c[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return tr


def atr(
    high: np.ndarray | list[float],
    low: np.ndarray | list[float],
    close: np.ndarray | list[float],
    period: int = 14,
) -> np.ndarray:
    """Average True Range (Wilder RMA of TR)."""
    tr = true_range(high, low, close)
    return rma(tr, period)


def macd(
    close: np.ndarray | list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    MACD line, signal line, histogram.

    Uses EMA for all components (common retail implementation).
    """
    c = _as_float(close)
    ema_fast = ema(c, fast)
    ema_slow = ema(c, slow)
    line = ema_fast - ema_slow
    sig = ema(line, signal)
    hist = line - sig
    return line, sig, hist


def rolling_std(values: np.ndarray | list[float], period: int) -> np.ndarray:
    """Population rolling standard deviation."""
    v = _as_float(values)
    n = len(v)
    out = np.full(n, np.nan)
    if period <= 0 or n < period:
        return out
    for i in range(period - 1, n):
        out[i] = float(np.std(v[i - period + 1 : i + 1], ddof=0))
    return out


def volume_spike_zscore(volume: np.ndarray | list[float], lookback: int = 20) -> np.ndarray:
    """
    Z-score of volume vs trailing mean/std (same lookback window).

    Values above ~2 suggest a spike vs recent baseline.
    """
    v = _as_float(volume)
    mu = sma(v, lookback)
    sd = rolling_std(v, lookback)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (v - mu) / sd
    # Flat volume window => std 0; treat z as 0 when defined.
    z = np.where(~np.isnan(sd) & (sd == 0.0), 0.0, z)
    return z


def volume_spike_flag(
    volume: np.ndarray | list[float],
    lookback: int = 20,
    *,
    z_threshold: float = 2.0,
) -> np.ndarray:
    """Boolean mask where `zscore > z_threshold` (False where z-score is undefined)."""
    z = volume_spike_zscore(volume, lookback)
    with np.errstate(invalid="ignore"):
        return z > z_threshold
