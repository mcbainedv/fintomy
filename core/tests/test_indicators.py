import numpy as np
import pandas as pd
import pytest

from fintomy_core import indicators as ind


def _series(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx, dtype="float64")


def test_sma_basic():
    s = _series([1, 2, 3, 4, 5])
    out = ind.sma(s, 3)
    assert np.isnan(out.iloc[0]) and np.isnan(out.iloc[1])
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[4] == pytest.approx(4.0)


def test_ema_converges_to_constant():
    s = _series([10.0] * 30)
    out = ind.ema(s, 10)
    assert out.dropna().iloc[-1] == pytest.approx(10.0)


def test_rsi_all_gains_is_high():
    s = _series(list(np.arange(1, 40, dtype="float64")))
    value = ind.last_valid(ind.rsi(s, 14))
    assert value is not None and value > 95


def test_rsi_all_losses_is_low():
    s = _series(list(np.arange(40, 1, -1, dtype="float64")))
    value = ind.last_valid(ind.rsi(s, 14))
    assert value is not None and value < 5


def test_macd_columns_and_length():
    s = _series(list(np.sin(np.linspace(0, 6, 100)) * 5 + 100))
    frame = ind.macd(s)
    assert list(frame.columns) == ["macd", "signal", "hist"]
    assert len(frame) == 100


def test_bollinger_bands_ordering():
    rng = np.random.default_rng(0)
    s = _series(list(100 + rng.normal(0, 2, 60)))
    bands = ind.bollinger(s, 20, 2)
    tail = bands.dropna()
    assert (tail["upper"] >= tail["mid"]).all()
    assert (tail["mid"] >= tail["lower"]).all()


def test_crossover_detects_up_and_down():
    fast = _series([1, 1, 3, 3, 1, 1])
    slow = _series([2, 2, 2, 2, 2, 2])
    out = ind.crossover(fast, slow)
    assert out.iloc[2] == 1   # crossed above
    assert out.iloc[4] == -1  # crossed below
    assert out.iloc[3] == 0


def test_last_valid_handles_empty():
    assert ind.last_valid(_series([np.nan, np.nan])) is None
