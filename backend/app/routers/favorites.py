from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fintomy_core.models import Company, Favorite
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def list_favorites(db: Session = Depends(get_db)):
    return {"tickers": sorted(db.scalars(select(Favorite.ticker)).all())}


@router.put("/{ticker}")
def add_favorite(ticker: str, db: Session = Depends(get_db)):
    if db.get(Company, ticker) is None:
        raise HTTPException(status_code=404, detail="Unknown ticker")
    if db.get(Favorite, ticker) is None:
        db.add(Favorite(ticker=ticker))
        db.commit()
    return {"ticker": ticker, "is_favorite": True}


@router.delete("/{ticker}")
def remove_favorite(ticker: str, db: Session = Depends(get_db)):
    fav = db.get(Favorite, ticker)
    if fav is not None:
        db.delete(fav)
        db.commit()
    return {"ticker": ticker, "is_favorite": False}
