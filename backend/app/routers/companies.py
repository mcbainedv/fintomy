from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fintomy_core.models import Company, Favorite
from fintomy_core.signals import ALLOWED_MA_PERIODS, DEFAULT_MA_PERIOD
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db
from ..services import get_analysis

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _validate_ma(ma_period: int) -> int:
    return ma_period if ma_period in ALLOWED_MA_PERIODS else DEFAULT_MA_PERIOD


@router.get("")
def list_companies(
    db: Session = Depends(get_db),
    region: str | None = Query(None, pattern="^(US|EU)$"),
    sector: str | None = None,
    favorites_only: bool = False,
    ma_period: int = DEFAULT_MA_PERIOD,
):
    ma_period = _validate_ma(ma_period)
    favorites = set(db.scalars(select(Favorite.ticker)).all())

    stmt = select(Company)
    if region:
        stmt = stmt.where(Company.region == region)
    if sector:
        stmt = stmt.where(Company.sector == sector)
    stmt = stmt.order_by(Company.ticker.asc())
    companies = db.scalars(stmt).all()

    items = []
    for c in companies:
        if favorites_only and c.ticker not in favorites:
            continue
        analysis = get_analysis(db, c.ticker, ma_period)
        items.append(
            {
                "ticker": c.ticker,
                "name": c.name,
                "region": c.region,
                "sector": c.sector,
                "currency": c.currency,
                "is_favorite": c.ticker in favorites,
                "close": analysis.close,
                "change_pct": analysis.change_pct,
                "signal": analysis.aggregate,
                "as_of": analysis.as_of.isoformat() if analysis.as_of else None,
            }
        )
    return {"count": len(items), "ma_period": ma_period, "items": items}


@router.get("/{ticker}")
def get_company(ticker: str, db: Session = Depends(get_db)):
    company = db.get(Company, ticker)
    if company is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    is_fav = db.get(Favorite, ticker) is not None
    return {
        "ticker": company.ticker,
        "name": company.name,
        "region": company.region,
        "sector": company.sector,
        "industry": company.industry,
        "exchange": company.exchange,
        "currency": company.currency,
        "description": company.description,
        "market_cap": company.market_cap,
        "beta": company.beta,
        "trailing_pe": company.trailing_pe,
        "forward_pe": company.forward_pe,
        "dividend_yield": company.dividend_yield,
        "week52_high": company.week52_high,
        "week52_low": company.week52_low,
        "is_favorite": is_fav,
        "fundamentals_updated_at": (
            company.fundamentals_updated_at.isoformat()
            if company.fundamentals_updated_at
            else None
        ),
    }


@router.get("/{ticker}/analysis")
def company_analysis(
    ticker: str,
    db: Session = Depends(get_db),
    ma_period: int = DEFAULT_MA_PERIOD,
):
    if db.get(Company, ticker) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    return get_analysis(db, ticker, _validate_ma(ma_period)).as_dict()
