from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fintomy_core.models import Company
from fintomy_core.queries import RANGE_DAYS
from fintomy_core.signals import ALLOWED_MA_PERIODS, DEFAULT_MA_PERIOD
from sqlalchemy.orm import Session

from ..deps import get_db
from ..services import get_chart_payload

router = APIRouter(prefix="/api/companies", tags=["chart"])


@router.get("/{ticker}/chart")
def company_chart(
    ticker: str,
    db: Session = Depends(get_db),
    ma_period: int = DEFAULT_MA_PERIOD,
    range: str = Query("1y"),
):
    if db.get(Company, ticker) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    ma_period = ma_period if ma_period in ALLOWED_MA_PERIODS else DEFAULT_MA_PERIOD
    range_key = range if range in RANGE_DAYS else "1y"
    return get_chart_payload(db, ticker, ma_period, range_key)
