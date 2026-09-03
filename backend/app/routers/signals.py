from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fintomy_core.models import Company, Favorite
from fintomy_core.signals import ALLOWED_MA_PERIODS, BUY, DEFAULT_MA_PERIOD, SELL
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db
from ..services import get_analysis

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
def list_signals(
    db: Session = Depends(get_db),
    ma_period: int = DEFAULT_MA_PERIOD,
    region: str | None = Query(None, pattern="^(US|EU)$"),
):
    ma_period = ma_period if ma_period in ALLOWED_MA_PERIODS else DEFAULT_MA_PERIOD
    favorites = set(db.scalars(select(Favorite.ticker)).all())

    stmt = select(Company)
    if region:
        stmt = stmt.where(Company.region == region)
    companies = db.scalars(stmt.order_by(Company.ticker)).all()

    buy: list[dict] = []
    sell: list[dict] = []
    for c in companies:
        analysis = get_analysis(db, c.ticker, ma_period)
        if analysis.aggregate not in (BUY, SELL):
            continue
        entry = {
            "ticker": c.ticker,
            "name": c.name,
            "region": c.region,
            "sector": c.sector,
            "close": analysis.close,
            "change_pct": analysis.change_pct,
            "is_favorite": c.ticker in favorites,
            "reasons": [
                f"{s.name}: {s.detail}" for s in analysis.indicators if s.signal == analysis.aggregate
            ],
            "votes": analysis.votes,
        }
        (buy if analysis.aggregate == BUY else sell).append(entry)

    buy.sort(key=lambda e: (-(e["votes"].get(BUY, 0)), e["ticker"]))
    sell.sort(key=lambda e: (-(e["votes"].get(SELL, 0)), e["ticker"]))
    return {"ma_period": ma_period, "buy": buy, "sell": sell}
