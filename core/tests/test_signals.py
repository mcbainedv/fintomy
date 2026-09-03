import numpy as np
import pandas as pd

from fintomy_core import signals


def _prices(closes):
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"close": closes}, index=idx)


def test_uptrend_breakout_triggers_buy_bias():
    # Long flat base then a sharp move up in the last few bars -> fresh SMA cross.
    closes = [100.0] * 42 + [101, 105, 112]
    analysis = signals.compute_analysis("TEST", _prices(closes), ma_period=14)
    assert analysis.close == 112
    names = {s.name: s.signal for s in analysis.indicators}
    assert names[f"SMA14 cross"] == signals.BUY
    assert analysis.aggregate in (signals.BUY, signals.HOLD)


def test_downtrend_breakdown_triggers_sell():
    closes = [100.0] * 42 + [99, 95, 88]
    analysis = signals.compute_analysis("TEST", _prices(closes), ma_period=14)
    names = {s.name: s.signal for s in analysis.indicators}
    assert names["SMA14 cross"] == signals.SELL


def test_rsi_overbought_marks_sell():
    closes = list(np.arange(1, 60, dtype="float64"))
    analysis = signals.compute_analysis("TEST", _prices(closes), ma_period=14)
    rsi_sig = next(s for s in analysis.indicators if s.name.startswith("RSI"))
    assert rsi_sig.signal == signals.SELL


def test_invalid_ma_period_falls_back():
    analysis = signals.compute_analysis("TEST", _prices([100.0] * 30), ma_period=99)
    assert analysis.ma_period == signals.DEFAULT_MA_PERIOD


def test_empty_prices_safe():
    analysis = signals.compute_analysis("TEST", pd.DataFrame(), ma_period=14)
    assert analysis.close is None
    assert analysis.aggregate == signals.HOLD


def test_change_pct_computed():
    analysis = signals.compute_analysis("TEST", _prices([100.0, 110.0]), ma_period=7)
    assert analysis.change_pct == 10.0


def test_markers_have_dates_and_types():
    closes = [100.0] * 30 + [102, 105, 108, 104, 99, 96]
    markers = signals.signal_markers(_prices(closes), ma_period=7)
    assert markers
    assert all("date" in m and m["type"] in (signals.BUY, signals.SELL) for m in markers)
