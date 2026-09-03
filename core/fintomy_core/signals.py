"""Buy / sell signal rules built on top of :mod:`fintomy_core.indicators`."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from . import indicators as ind

BUY = "BUY"
SELL = "SELL"
HOLD = "HOLD"

ALLOWED_MA_PERIODS = (7, 14, 28)
DEFAULT_MA_PERIOD = 14

RSI_OVERSOLD = 30.0
RSI_OVERBOUGHT = 70.0

# A crossover counts as an active signal if it happened within this many trading
# days of the latest bar (so a Friday cross is still "fresh" on Monday).
SIGNAL_LOOKBACK = 3


def _recent_cross(cross: pd.Series, lookback: int = SIGNAL_LOOKBACK) -> int:
    """Return +1/-1 for the most recent crossover within ``lookback`` bars, else 0."""
    tail = cross.iloc[-lookback:]
    for value in reversed(tail.tolist()):
        if value != 0:
            return int(value)
    return 0


@dataclass
class IndicatorSignal:
    name: str
    signal: str  # BUY | SELL | HOLD
    detail: str = ""


@dataclass
class Analysis:
    ticker: str
    as_of: date | None
    ma_period: int
    close: float | None
    prev_close: float | None
    change_pct: float | None
    indicators: list[IndicatorSignal] = field(default_factory=list)
    aggregate: str = HOLD
    votes: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "as_of": self.as_of.isoformat() if self.as_of else None,
            "ma_period": self.ma_period,
            "close": self.close,
            "prev_close": self.prev_close,
            "change_pct": self.change_pct,
            "aggregate": self.aggregate,
            "votes": self.votes,
            "indicators": [
                {"name": s.name, "signal": s.signal, "detail": s.detail}
                for s in self.indicators
            ],
        }


def _sma_cross_signal(close: pd.Series, ma_period: int) -> IndicatorSignal:
    line = ind.sma(close, ma_period)
    cross = ind.crossover(close, line)
    last = _recent_cross(cross)
    if last > 0:
        return IndicatorSignal(f"SMA{ma_period} cross", BUY, "price crossed above SMA")
    if last < 0:
        return IndicatorSignal(f"SMA{ma_period} cross", SELL, "price crossed below SMA")
    # No cross today -> use position relative to the average as a weak bias.
    price = ind.last_valid(close)
    avg = ind.last_valid(line)
    if price is not None and avg is not None:
        detail = "price above SMA" if price >= avg else "price below SMA"
        return IndicatorSignal(f"SMA{ma_period} cross", HOLD, detail)
    return IndicatorSignal(f"SMA{ma_period} cross", HOLD, "insufficient history")


def _rsi_signal(close: pd.Series, period: int = 14) -> IndicatorSignal:
    value = ind.last_valid(ind.rsi(close, period))
    if value is None:
        return IndicatorSignal(f"RSI{period}", HOLD, "insufficient history")
    if value <= RSI_OVERSOLD:
        return IndicatorSignal(f"RSI{period}", BUY, f"oversold ({value:.1f})")
    if value >= RSI_OVERBOUGHT:
        return IndicatorSignal(f"RSI{period}", SELL, f"overbought ({value:.1f})")
    return IndicatorSignal(f"RSI{period}", HOLD, f"neutral ({value:.1f})")


def _macd_signal(close: pd.Series) -> IndicatorSignal:
    frame = ind.macd(close)
    cross = ind.crossover(frame["macd"], frame["signal"])
    last = _recent_cross(cross)
    if last > 0:
        return IndicatorSignal("MACD", BUY, "MACD crossed above signal")
    if last < 0:
        return IndicatorSignal("MACD", SELL, "MACD crossed below signal")
    hist = ind.last_valid(frame["hist"])
    if hist is None:
        return IndicatorSignal("MACD", HOLD, "insufficient history")
    return IndicatorSignal("MACD", HOLD, "histogram " + ("positive" if hist >= 0 else "negative"))


def _bollinger_signal(close: pd.Series) -> IndicatorSignal:
    bands = ind.bollinger(close)
    price = ind.last_valid(close)
    lower = ind.last_valid(bands["lower"])
    upper = ind.last_valid(bands["upper"])
    if price is None or lower is None or upper is None:
        return IndicatorSignal("Bollinger", HOLD, "insufficient history")
    if price <= lower:
        return IndicatorSignal("Bollinger", BUY, "price at/below lower band")
    if price >= upper:
        return IndicatorSignal("Bollinger", SELL, "price at/above upper band")
    return IndicatorSignal("Bollinger", HOLD, "inside bands")


def compute_analysis(
    ticker: str,
    prices: pd.DataFrame,
    ma_period: int = DEFAULT_MA_PERIOD,
) -> Analysis:
    """``prices`` must be indexed by date and contain a ``close`` column, sorted ascending."""
    if ma_period not in ALLOWED_MA_PERIODS:
        ma_period = DEFAULT_MA_PERIOD

    if prices is None or prices.empty or "close" not in prices:
        return Analysis(ticker, None, ma_period, None, None, None)

    prices = prices.sort_index()
    close = prices["close"].astype(float)

    as_of = prices.index[-1]
    if hasattr(as_of, "date"):
        as_of = as_of.date()

    last_close = ind.last_valid(close)
    prev_close = float(close.iloc[-2]) if len(close) >= 2 else None
    change_pct = None
    if last_close is not None and prev_close not in (None, 0):
        change_pct = round((last_close - prev_close) / prev_close * 100.0, 2)

    signals = [
        _sma_cross_signal(close, ma_period),
        _rsi_signal(close),
        _macd_signal(close),
        _bollinger_signal(close),
    ]

    votes = {BUY: 0, SELL: 0, HOLD: 0}
    for s in signals:
        votes[s.signal] += 1

    if votes[BUY] > votes[SELL] and votes[BUY] >= 2:
        aggregate = BUY
    elif votes[SELL] > votes[BUY] and votes[SELL] >= 2:
        aggregate = SELL
    else:
        aggregate = HOLD

    return Analysis(
        ticker=ticker,
        as_of=as_of,
        ma_period=ma_period,
        close=last_close,
        prev_close=prev_close,
        change_pct=change_pct,
        indicators=signals,
        aggregate=aggregate,
        votes=votes,
    )


def signal_markers(prices: pd.DataFrame, ma_period: int) -> list[dict]:
    """Historical BUY/SELL markers for charting (SMA cross + MACD cross)."""
    if prices is None or prices.empty or "close" not in prices:
        return []
    prices = prices.sort_index()
    close = prices["close"].astype(float)

    sma_cross = ind.crossover(close, ind.sma(close, ma_period))
    m = ind.macd(close)
    macd_cross = ind.crossover(m["macd"], m["signal"])

    markers: list[dict] = []
    for idx, value in sma_cross.items():
        if value != 0:
            d = idx.date() if hasattr(idx, "date") else idx
            markers.append(
                {
                    "date": d.isoformat(),
                    "type": BUY if value > 0 else SELL,
                    "source": f"SMA{ma_period}",
                }
            )
    for idx, value in macd_cross.items():
        if value != 0:
            d = idx.date() if hasattr(idx, "date") else idx
            markers.append(
                {
                    "date": d.isoformat(),
                    "type": BUY if value > 0 else SELL,
                    "source": "MACD",
                }
            )
    markers.sort(key=lambda x: x["date"])
    return markers
