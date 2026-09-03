"""Technical indicators computed on a pandas Series of closing prices.

Every function returns a pandas object aligned to the input index, with leading
``NaN`` where there is not enough history.  Keep these pure and side-effect free
so they are trivially unit-testable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, period: int) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window=period, min_periods=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    """Exponential moving average."""
    return close.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss == 0 the ratio is inf -> RSI 100; when both are 0 -> NaN stays.
    out = out.where(avg_loss != 0, other=100.0)
    out = out.where(~((avg_gain == 0) & (avg_loss == 0)), other=50.0)
    return out


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD line, signal line and histogram.

    Returns a DataFrame with columns ``macd``, ``signal``, ``hist``.
    """
    fast_ema = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_ema = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger(
    close: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands. Returns columns ``mid``, ``upper``, ``lower``."""
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    return pd.DataFrame(
        {
            "mid": mid,
            "upper": mid + num_std * std,
            "lower": mid - num_std * std,
        }
    )


def crossover(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """+1 where ``fast`` crosses above ``slow``, -1 where it crosses below, else 0."""
    diff = fast - slow
    prev = diff.shift(1)
    up = (prev <= 0) & (diff > 0)
    down = (prev >= 0) & (diff < 0)
    out = pd.Series(0, index=fast.index, dtype="int64")
    out[up] = 1
    out[down] = -1
    # Rows where either side is NaN cannot be a cross.
    out[diff.isna() | prev.isna()] = 0
    return out


def last_valid(series: pd.Series) -> float | None:
    """Return the last non-NaN float value, or ``None``."""
    s = series.dropna()
    if s.empty:
        return None
    val = float(s.iloc[-1])
    return None if np.isnan(val) else val
