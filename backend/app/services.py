"""Business logic shared across routers."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from fintomy_core import indicators as ind
from fintomy_core import signals
from fintomy_core.queries import load_prices, range_to_start
from sqlalchemy.orm import Session

from .cache import get_or_set


def _num(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else round(f, 4)


def _series_points(index: pd.DatetimeIndex, series: pd.Series) -> list[dict]:
    out = []
    for ts, value in zip(index, series.tolist()):
        v = _num(value)
        if v is None:
            continue
        out.append({"date": ts.date().isoformat(), "value": v})
    return out


def get_analysis(db: Session, ticker: str, ma_period: int) -> signals.Analysis:
    """Signal summary for one ticker (cached ~5 min)."""

    def produce() -> signals.Analysis:
        frame = load_prices(db, ticker)
        return signals.compute_analysis(ticker, frame, ma_period)

    return get_or_set(("analysis", ticker, ma_period), produce)


def get_chart_payload(db: Session, ticker: str, ma_period: int, range_key: str) -> dict:
    def produce() -> dict:
        start = range_to_start(range_key)
        frame = load_prices(db, ticker, start=start)
        if frame.empty:
            return {
                "ticker": ticker,
                "ma_period": ma_period,
                "range": range_key,
                "candles": [],
                "sma": [],
                "rsi": [],
                "macd": [],
                "bollinger": {"upper": [], "lower": []},
                "markers": [],
            }

        frame = frame.sort_index()
        close = frame["close"].astype(float)
        macd_frame = ind.macd(close)
        boll = ind.bollinger(close)

        candles = []
        for ts, rec in frame.iterrows():
            c = _num(rec["close"])
            if c is None:
                continue
            candles.append(
                {
                    "date": ts.date().isoformat(),
                    "open": _num(rec["open"]) if _num(rec["open"]) is not None else c,
                    "high": _num(rec["high"]) if _num(rec["high"]) is not None else c,
                    "low": _num(rec["low"]) if _num(rec["low"]) is not None else c,
                    "close": c,
                    "volume": int(rec["volume"]) if not pd.isna(rec["volume"]) else 0,
                }
            )

        return {
            "ticker": ticker,
            "ma_period": ma_period,
            "range": range_key,
            "candles": candles,
            "sma": _series_points(frame.index, ind.sma(close, ma_period)),
            "rsi": _series_points(frame.index, ind.rsi(close, 14)),
            "macd": [
                {
                    "date": ts.date().isoformat(),
                    "macd": _num(m),
                    "signal": _num(s),
                    "hist": _num(h),
                }
                for ts, m, s, h in zip(
                    frame.index,
                    macd_frame["macd"].tolist(),
                    macd_frame["signal"].tolist(),
                    macd_frame["hist"].tolist(),
                )
                if _num(m) is not None
            ],
            "bollinger": {
                "upper": _series_points(frame.index, boll["upper"]),
                "lower": _series_points(frame.index, boll["lower"]),
            },
            "markers": signals.signal_markers(frame, ma_period),
        }

    return get_or_set(("chart", ticker, ma_period, range_key), produce)
