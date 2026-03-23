"""Unit tests for `app.market_data.indicators` (pure NumPy)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.market_data import indicators as ind


def test_sma_simple() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    out = ind.sma(x, 3)
    assert math.isnan(out[0]) and math.isnan(out[1])
    assert out[2] == pytest.approx(2.0)
    assert out[3] == pytest.approx(3.0)
    assert out[4] == pytest.approx(4.0)


def test_ema_monotonic_increases() -> None:
    x = np.linspace(10.0, 20.0, 50)
    e = ind.ema(x, 10)
    assert e[0] == pytest.approx(10.0)
    assert e[-1] > e[0]


def test_rsi_all_up_closes_high() -> None:
    """Strong upward drift should push RSI toward 100 on warm bars."""
    c = np.cumsum(np.ones(40)) + 50.0  # monotone up
    r = ind.rsi(c, period=14)
    assert np.isnan(r[:13]).all()
    assert not np.isnan(r[13])
    assert r[-1] > 90.0


def test_rsi_flat_near_fifty() -> None:
    c = np.ones(40) * 5.0
    r = ind.rsi(c, period=14)
    assert r[-1] == pytest.approx(50.0)


def test_macd_shapes() -> None:
    c = np.cumsum(np.random.default_rng(0).normal(0, 0.1, size=80)) + 100.0
    line, sig, hist = ind.macd(c, fast=12, slow=26, signal=9)
    assert len(line) == len(c) == len(sig) == len(hist)


def test_atr_non_negative() -> None:
    n = 50
    rng = np.random.default_rng(1)
    h = 100 + np.cumsum(rng.normal(0, 0.2, n))
    l = h - np.abs(rng.normal(0.5, 0.1, n))
    c = (h + l) / 2.0
    a = ind.atr(h, l, c, period=14)
    valid = a[~np.isnan(a)]
    assert (valid >= 0).all()


def test_volume_spike_zscore_detects_spike() -> None:
    v = np.ones(40) * 1e6
    v[-1] = 5e6
    z = ind.volume_spike_zscore(v, lookback=20)
    assert z[-1] > 3.0


def test_volume_spike_flag() -> None:
    v = np.ones(30) * 100.0
    v[-1] = 500.0
    f = ind.volume_spike_flag(v, lookback=10, z_threshold=2.0)
    assert bool(f[-1]) is True
    assert bool(f[0]) is False
