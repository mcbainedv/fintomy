from __future__ import annotations

from fastapi import APIRouter, Depends
from fintomy_core.models import Company, Price, ScrapeRun
from fintomy_core.queries import RANGE_DAYS
from fintomy_core.signals import ALLOWED_MA_PERIODS, DEFAULT_MA_PERIOD
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from ..deps import get_db

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    sectors = sorted(x for x in db.scalars(select(distinct(Company.sector))).all() if x)
    regions = sorted(x for x in db.scalars(select(distinct(Company.region))).all() if x)
    company_count = db.scalar(select(func.count(Company.ticker)))
    price_count = db.scalar(select(func.count(Price.id)))
    latest_price_date = db.scalar(select(func.max(Price.date)))
    last_ok = db.scalar(
        select(ScrapeRun).where(ScrapeRun.status == "ok").order_by(ScrapeRun.id.desc()).limit(1)
    )
    return {
        "sectors": sectors,
        "regions": regions,
        "company_count": company_count,
        "price_count": price_count,
        "latest_price_date": latest_price_date.isoformat() if latest_price_date else None,
        "last_successful_scrape": last_ok.finished_at.isoformat()
        if last_ok and last_ok.finished_at
        else None,
        "ma_periods": list(ALLOWED_MA_PERIODS),
        "default_ma_period": DEFAULT_MA_PERIOD,
        "ranges": list(RANGE_DAYS.keys()),
    }


@router.get("/health")
def health():
    return {"status": "ok"}
