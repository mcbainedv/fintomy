"""Read helpers shared by the API layer."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Price

RANGE_DAYS = {
    "1mo": 31,
    "3mo": 93,
    "6mo": 186,
    "1y": 366,
    "2y": 731,
    "5y": 1827,
    "max": 100_000,
}


def range_to_start(range_key: str) -> date:
    days = RANGE_DAYS.get(range_key, RANGE_DAYS["1y"])
    return date.today() - timedelta(days=days)


def load_prices(session: Session, ticker: str, start: date | None = None) -> pd.DataFrame:
    """Return a DataFrame indexed by date with OHLCV columns, sorted ascending."""
    stmt = select(
        Price.date, Price.open, Price.high, Price.low, Price.close, Price.adj_close, Price.volume
    ).where(Price.ticker == ticker)
    if start is not None:
        stmt = stmt.where(Price.date >= start)
    stmt = stmt.order_by(Price.date.asc())

    rows = session.execute(stmt).all()
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "adj_close", "volume"])

    frame = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "adj_close", "volume"])
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.set_index("date")
    for col in ("open", "high", "low", "close", "adj_close"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce")
    return frame
